import json
import time
import threading
import secrets
import hmac
import hashlib
from contextlib import contextmanager
from pathlib import Path

SECRET_KEY = b'shared-bank-secret'
BANK_FILE = Path(__file__).with_name('bank.json')
_lock = threading.Lock()

def _sign(transfers: dict) -> str:
    data = json.dumps({'transfers': transfers}, sort_keys=True).encode()
    return hmac.new(SECRET_KEY, data, hashlib.sha256).hexdigest()

def _save(data: dict) -> None:
    transfers = data.get('transfers', {})
    payload = {'transfers': transfers, 'signature': _sign(transfers)}
    with open(BANK_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

def _load() -> dict:
    if not BANK_FILE.exists():
        _save({'transfers': {}})
    with open(BANK_FILE, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    transfers = payload.get('transfers', {})
    signature = payload.get('signature', '')
    if _sign(transfers) != signature:
        raise ValueError('Bank data signature mismatch')
    return {'transfers': transfers}

@contextmanager
def _access_bank():
    with _lock:
        data = _load()
        yield data
        _save(data)

def create_transfer(user_id: str, amount: int, from_app: str, to_app: str) -> str:
    if not isinstance(amount, int) or amount <= 0:
        raise ValueError('Amount must be positive integer')
    with _access_bank() as bank:
        transfers = bank['transfers']
        while True:
            code = secrets.token_hex(3).upper()
            if code not in transfers:
                break
        transfers[code] = {
            'code': code,
            'from_app': from_app,
            'to_app': to_app,
            'user_id': user_id,
            'amount': amount,
            'timestamp': time.time(),
            'claimed': False,
        }
        return code

def claim_transfer(code: str, expect_to_app: str, user_id: str) -> int:
    with _access_bank() as bank:
        t = bank['transfers'].get(code)
        if not t:
            raise ValueError('Invalid code')
        if t['claimed']:
            raise ValueError('Code already claimed')
        if t['to_app'] != expect_to_app:
            raise ValueError('Wrong destination')
        if t['user_id'] != user_id:
            raise ValueError('User mismatch')
        t['claimed'] = True
        return t['amount']

def peek_transfer(code: str):
    with _lock:
        data = _load()
    return data['transfers'].get(code)
