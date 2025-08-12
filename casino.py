import json
import os
import random
import subprocess
import sys
import bank

SAVE_FILE = 'casino_save.json'


def load_wallet():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('wallet', 100)
    return 100


def save_wallet(wallet):
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'wallet': wallet}, f, indent=2)


def bank_menu(wallet):
    user_id = 'player1'
    while True:
        print(f"\n--- Bank ---\nWallet: {wallet}$")
        action = input('(P) Pay, (R) Receive, (B) Back: ').strip().upper()
        if action == 'P':
            try:
                amount = int(input('Amount to send: '))
            except ValueError:
                print('Invalid amount.')
                continue
            if amount <= 0 or amount > wallet:
                print('Amount exceeds wallet.')
                continue
            wallet -= amount
            save_wallet(wallet)
            code = bank.create_transfer(user_id, amount, 'casino', 'fishing')
            print(f'Transfer code: {code}')
            print('Launching fishing game...')
            subprocess.Popen([sys.executable, 'fishing.py'])
            sys.exit(0)
        elif action == 'R':
            code = input('Enter code: ').strip().upper()
            try:
                amount = bank.claim_transfer(code, 'casino', user_id)
            except Exception as e:
                print(f'Error: {e}')
                continue
            wallet += amount
            save_wallet(wallet)
            print(f'Received {amount}$.')
        elif action == 'B':
            break
        else:
            print('Invalid choice.')
    return wallet


def main():
    wallet = load_wallet()
    while True:
        print(f"\n--- Casino ---\nWallet: {wallet}$")
        print('1. Coin Flip (bet 10)')
        print('2. Bank')
        print('3. Exit')
        choice = input('Choose: ').strip()
        if choice == '1':
            if wallet < 10:
                print('Not enough money.')
                continue
            if random.random() < 0.5:
                wallet += 10
                print('You won 10!')
            else:
                wallet -= 10
                print('You lost 10!')
            save_wallet(wallet)
        elif choice == '2':
            wallet = bank_menu(wallet)
        elif choice == '3':
            save_wallet(wallet)
            break
        else:
            print('Invalid choice.')


if __name__ == '__main__':
    main()
