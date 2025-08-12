import json
import os
import random
import subprocess
import sys
import time
from typing import Optional

import bank

SAVE_FILE = 'casino_save.json'


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def prompt_int(label: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    while True:
        try:
            value = int(input(label))
        except ValueError:
            print('Enter a valid number.')
            continue
        if min_value is not None and value < min_value:
            print(f'Value must be >= {min_value}.')
            continue
        if max_value is not None and value > max_value:
            print(f'Value must be <= {max_value}.')
            continue
        return value


def launch_other_game(target: str) -> None:
    subprocess.Popen([sys.executable, target])


def load_wallet() -> int:
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('wallet', 100)
    return 100


def save_wallet(wallet: int) -> None:
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'wallet': wallet}, f, indent=2)


def bank_menu(wallet: int) -> int:
    user_id = 'player1'
    while True:
        print(f"\n--- Bank ---\nWallet: {wallet}$")
        action = input('(P) Pay, (R) Receive, (B) Back: ').strip().upper()
        if action == 'P':
            amount = prompt_int('Amount to send: ', 1, wallet)
            wallet -= amount
            save_wallet(wallet)
            code = bank.create_transfer(user_id, amount, 'casino', 'fishing')
            print(f'Transfer code: {code}')
            print('Launching fishing game...')
            launch_other_game('fishing.py')
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


def get_bet(wallet: int) -> int:
    while True:
        bet = prompt_int('Bet amount (>100): ')
        if bet <= 100:
            print('Bet must be > 100.')
        elif bet > wallet:
            print('Not enough funds.')
        else:
            return bet


def game_one_or_two(wallet: int) -> int:
    print('\n--- One or Two ---')
    print(f'Wallet: {wallet}$')
    bet = get_bet(wallet)
    pick = prompt_int('Pick 1 or 2: ', 1, 2)
    wallet -= bet
    draw = random.randint(1, 2)
    if pick == draw:
        wallet += bet * 2
        print(f'WIN! You receive {bet * 2}$.')
    else:
        print('LOSE!')
    save_wallet(wallet)
    return wallet


def horse_race(wallet: int) -> int:
    print('\n--- Horse Race ---')
    print(f'Wallet: {wallet}$')
    bet = get_bet(wallet)
    horses = ['A', 'B', 'C']
    choice = input('Choose horse (A/B/C): ').strip().upper()
    while choice not in horses:
        choice = input('Choose horse (A/B/C): ').strip().upper()
    wallet -= bet
    positions = {h: 0 for h in horses}
    finish = 20
    while True:
        clear_screen()
        for h in horses:
            positions[h] += random.randint(0, 2)
            track = '-' * positions[h]
            print(f'{h}: {track}')
        time.sleep(0.3)
        if max(positions.values()) >= finish:
            break
    winner = max(horses, key=lambda h: positions[h])
    print(f'Winner: {winner}')
    if choice == winner:
        wallet += bet * 2
        print(f'Your horse won! You receive {bet * 2}$.')
    else:
        print('Your horse lost.')
    save_wallet(wallet)
    return wallet


def random_spin(wallet: int) -> int:
    print('\n--- RANDOM ---')
    print(f'Wallet: {wallet}$')
    if wallet < 1000:
        print('Not enough funds (need 1000$).')
        return wallet
    wallet -= 1000
    if random.randint(0, 1) == 1:
        wallet += 2000
        print('Paid 1000 → Won 2000 (WIN)')
    else:
        print('Paid 1000 → Won 0 (LOSE)')
    save_wallet(wallet)
    return wallet


def main() -> None:
    wallet = load_wallet()
    while True:
        print('\nPick your choice [1-13]')
        print(f'Wallet: {wallet}$')
        print('1. Start Fishing')
        print('2. Fast Fishing')
        print('3. Quests')
        print('4. Inventory')
        print('5. Shop')
        print('6. Discovery Log')
        print('7. Travel / Zones')
        print('8. Settings / Daily info')
        print('9. Statistics / Achievements')
        print('10. BANK (Pay / Receive)')
        print('11. One or Two')
        print('12. Horse Race')
        print('13. RANDOM')
        print('0. Exit')
        choice = input('Choose: ').strip()
        if choice in {'1', '2', '3', '4', '5', '6', '7', '8', '9'}:
            print('Launching fishing game...')
            launch_other_game('fishing.py')
            sys.exit(0)
        elif choice == '10':
            wallet = bank_menu(wallet)
        elif choice == '11':
            wallet = game_one_or_two(wallet)
        elif choice == '12':
            wallet = horse_race(wallet)
        elif choice == '13':
            wallet = random_spin(wallet)
        elif choice == '0':
            save_wallet(wallet)
            break
        else:
            print('Invalid choice.')


if __name__ == '__main__':
    main()

