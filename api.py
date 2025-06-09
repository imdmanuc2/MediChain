import os
import hashlib
import json
import csv
import uuid
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, flash, session, abort
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from auth import User, verify_user, register_user, load_users, is_admin_user
from medichain import Blockchain
from wallet import get_wallet, update_wallet
from PIL import Image
import pytesseract
import config
from functools import wraps

active_network = config.ACTIVE_NETWORK  # 'testnet' or 'mainnet'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
medichain = Blockchain()

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.jinja_env.globals.update(
    config=config,
    current_user=current_user,
    is_admin_user=is_admin_user
)

def is_admin():
    return is_admin_user(session.get('patient_id'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(username):
    return User(username)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def save_chain_to_json(filename=None):
    if not filename:
        filename = config.CHAIN_FILE
    with open(filename, 'w') as f:
        json.dump(medichain.to_dict(), f, indent=4)

def run_ocr(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path))
    except Exception as e:
        return f"OCR error: {str(e)}"

def extract_medications_allergies(text):
    lines = text.lower().splitlines()
    meds = [line for line in lines if 'med' in line or 'rx' in line]
    allergies = [line for line in lines if 'allerg' in line]
    return meds, allergies

@app.route('/')
def dashboard():
    if session.get('patient_id'):
        wallet = get_wallet(session.get('patient_id'))
        return render_template('dashboard.html', chain=medichain.to_dict(), wallet=wallet)
    return render_template('index.html')

@app.route('/wallet')
@login_required
def wallet_page():
    patient_id = session.get('patient_id')
    wallet = get_wallet(patient_id)
    return render_template('wallet.html', wallet=wallet)

@app.route('/index')
def public_index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if verify_user(username, password):
            login_user(User(username))
            session['patient_id'] = username
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if register_user(username, password):
            session['patient_id'] = str(uuid.uuid4())
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        flash('Username already exists.')
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    files = request.files.getlist('file')
    uploaded_files = []
    file_hashes = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            uploaded_files.append(url_for('uploaded_file', filename=filename))
            file_hashes.append(sha256_file(path))

    is_payment = request.form.get('is_payment')
    patient_id = request.form.get('patient_id') or session.get('patient_id', 'unknown')

    visit_record = {
        'patient_id': patient_id,
        'provider': request.form.get('provider', 'unknown'),
        'doctor': request.form.get('doctor', 'unknown'),
        'location': request.form.get('location', 'unknown'),
        'date': request.form.get('date', 'unknown'),
        'type': request.form.get('type', 'General'),
        'notes': request.form.get('notes', ''),
        'medications': request.form.get('medications', ''),
        'allergies': request.form.get('allergies', ''),
        'file_paths': uploaded_files,
        'file_hashes': file_hashes
    }

    if is_payment:
        visit_record.update({
            'type': 'Payment',
            'billed_amount': request.form.get('billed_amount', '0'),
            'amount_paid': request.form.get('amount_paid', '0'),
            'payment_date': request.form.get('payment_date', ''),
            'payment_notes': request.form.get('payment_notes', '')
        })

    medichain.add_block(visit_record)

    reward_amount = config.REWARD_AMOUNT
    reward_tx = {
        'type': 'Reward',
        'patient_id': patient_id,
        'amount': reward_amount,
        'reason': 'Upload',
        'tx_id': str(uuid.uuid4())
    }
    medichain.add_block(reward_tx)
    update_wallet(patient_id, reward_amount, 'upload')

    save_chain_to_json()
    return redirect('/')

@app.route('/ocr-preview', methods=['POST'])
@login_required
def ocr_preview():
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files provided'}), 400

    all_text = ''
    for file in files:
        if allowed_file(file.filename):
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + secure_filename(file.filename))
            file.save(temp_path)
            all_text += run_ocr(temp_path) + '\n'
            os.remove(temp_path)

    meds, allergies = extract_medications_allergies(all_text)

    return jsonify({
        'medications': meds,
        'allergies': allergies,
        'raw_text': all_text
    })

@app.route('/history/<patient_id>', methods=['GET'])
@login_required
def patient_history(patient_id):
    app.logger.info(f"{current_user.id} accessed history for {patient_id}")
    chain = medichain.to_dict()
    records = [block for block in chain if block['data'].get('patient_id') == patient_id]
    return render_template('history.html', patient_id=patient_id, records=records)

@app.route('/history/<patient_id>/json')
@login_required
def download_json(patient_id):
    chain = medichain.to_dict()
    records = [block for block in chain if block['data'].get('patient_id') == patient_id]
    return jsonify(records)

@app.route('/history/<patient_id>/csv')
@login_required
def download_csv(patient_id):
    chain = medichain.to_dict()
    records = [block['data'] for block in chain if block['data'].get('patient_id') == patient_id]
    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{patient_id}_history.csv')
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(csv_file), as_attachment=True)

@app.route('/chain', methods=['GET'])
@login_required
def get_chain():
    return jsonify(medichain.to_dict())

@app.route('/validate', methods=['GET'])
@login_required
def validate():
    return jsonify({"valid": medichain.is_chain_valid()})

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/switch-network/<network>')
@admin_required
def switch_network(network):
    global active_network, medichain
    if network not in config.NETWORKS:
        flash(f"Unknown network: {network}")
        return redirect(url_for('dashboard'))

    active_network = network
    chain_file = config.NETWORKS[active_network]['CHAIN_FILE']

    if os.path.exists(chain_file):
        with open(chain_file, 'r') as f:
            medichain.load_from_dict(json.load(f))
    else:
        medichain = Blockchain()
        save_chain_to_json()

    flash(f"Switched to {active_network} network.")
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = load_users()
    chain_summary = {
        'length': len(medichain.chain),
        'latest_hash': medichain.get_latest_block().hash,
        'valid': medichain.is_chain_valid(),
        'network': active_network
    }
    network_config = config.NETWORKS[active_network]
    return render_template("admin/admin_panel.html", users=users, chain=chain_summary, network_config=network_config)

@app.route('/admin/cli', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_cli():
    output = ""
    if request.method == 'POST':
        cmd = request.form.get('command', '')
        if cmd.startswith('view-wallet'):
            try:
                _, pid = cmd.split()
                wallet = get_wallet(pid)
                output = json.dumps(wallet, indent=2) if wallet else 'Wallet not found'
            except Exception as e:
                output = f"Error: {str(e)}"
        elif cmd == 'flush-chain':
            medichain.chain = [medichain.create_genesis_block()]
            save_chain_to_json()
            output = 'Chain reset to genesis block.'
        elif cmd == 'validate':
            output = f"Valid: {medichain.is_chain_valid()}"
        else:
            output = 'Unknown command'

    return render_template("admin/admin_cli.html", output=output)

@app.route('/admin/reset-wallet', methods=['POST'])
@admin_required
def admin_reset_wallet():
    patient_id = request.form.get('patient_id')
    if not patient_id:
        flash("Missing patient ID.")
        return redirect(url_for('admin_panel'))

    update_wallet(patient_id, 0, reason='admin_reset')
    flash(f"Wallet for {patient_id} has been reset.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/add-admin', methods=['POST'])
@admin_required
def admin_add_admin():
    new_admin = request.form.get('new_admin')
    users = load_users()
    if new_admin in users:
        users[new_admin]['admin'] = True
        with open(config.USER_DB, 'w') as f:
            json.dump(users, f, indent=4)
        flash(f"{new_admin} is now an admin.")
    else:
        flash("User not found.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/remove-admin', methods=['POST'])
@admin_required
def admin_remove_admin():
    remove_admin = request.form.get('remove_admin')
    users = load_users()
    if remove_admin in users and users[remove_admin].get('admin'):
        users[remove_admin]['admin'] = False
        with open(config.USER_DB, 'w') as f:
            json.dump(users, f, indent=4)
        flash(f"{remove_admin} is no longer an admin.")
    else:
        flash("User not found or not an admin.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
