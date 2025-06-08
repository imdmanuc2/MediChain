# wallet.py
import os
import json
from datetime import datetime

WALLET_FILE = 'wallet.json'

def load_wallets():
    if not os.path.exists(WALLET_FILE):
        return {}
    with open(WALLET_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_wallets(wallets):
    with open(WALLET_FILE, 'w') as f:
        json.dump(wallets, f, indent=4)

def get_wallet(patient_id):
    wallets = load_wallets()
    return wallets.get(patient_id, {
        'patient_id': patient_id,
        'balance': 0.0,
        'uploads': 0,
        'earned': 0.0,
        'transactions': []
    })

def update_wallet(patient_id, amount, tx_type='upload'):
    wallets = load_wallets()
    wallet = wallets.get(patient_id, get_wallet(patient_id))

    wallet['balance'] = round(wallet.get('balance', 0.0) + amount, 8)
    wallet['earned'] = round(wallet.get('earned', 0.0) + amount, 8)
    if tx_type == 'upload':
        wallet['uploads'] = wallet.get('uploads', 0) + 1

    wallet.setdefault('transactions', []).append({
        'amount': round(amount, 8),
        'type': tx_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

    wallets[patient_id] = wallet
    save_wallets(wallets)
    return wallet
