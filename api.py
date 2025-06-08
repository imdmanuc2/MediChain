import os
import hashlib
import json
import csv
import uuid
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, flash, session
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from auth import User, verify_user, register_user
from medichain import Blockchain
from wallet import get_wallet, update_wallet
from PIL import Image
import pytesseract

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

def save_chain_to_json(filename='blockchain.json'):
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
@login_required
def dashboard():
    patient_id = session.get('patient_id')
    wallet = get_wallet(patient_id)
    return render_template('dashboard.html', chain=medichain.to_dict(), wallet=wallet)

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

    reward_amount = 1.0
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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
