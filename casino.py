import json
import os
import random
import subprocess
import sys
import time

import bank

SAVE_FILE = "casino_save.json"


def load_wallet() -> int:
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("wallet", 100)
    return 100


def save_wallet(wallet: int) -> None:
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"wallet": wallet}, f, indent=2)


def one_or_two(wallet: int) -> int:
    print("\n--- One or Two ---")
    print(f"Wallet: {wallet}$")
    if wallet <= 100:
        print("Need at least 101$ to play.")
        return wallet
    while True:
        try:
            bet = int(input("Bet amount (>100): "))
        except ValueError:
            print("Invalid amount.")
            continue
        if bet <= 100 or bet > wallet:
            print("Bet must be >100 and ≤ wallet.")
            continue
        break
    while True:
        guess = input("Pick 1 or 2: ").strip()
        if guess in ("1", "2"):
            break
        print("Invalid choice. Enter 1 or 2.")
    result = str(random.randint(1, 2))
    wallet -= bet
    if guess == result:
        winnings = bet * 2
        wallet += winnings
        print(f"Number was {result}. You win {winnings}$!")
    else:
        print(f"Number was {result}. You lose {bet}$.")
    save_wallet(wallet)
    return wallet


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def horse_race(wallet: int) -> int:
    print("\n--- Horse Race ---")
    print(f"Wallet: {wallet}$")
    if wallet <= 100:
        print("Need at least 101$ to play.")
        return wallet
    while True:
        try:
            bet = int(input("Bet amount (>100): "))
        except ValueError:
            print("Invalid amount.")
            continue
        if bet <= 100 or bet > wallet:
            print("Bet must be >100 and ≤ wallet.")
            continue
        break
    horses = ["A", "B", "C"]
    while True:
        pick = input("Choose your horse (A/B/C): ").strip().upper()
        if pick in horses:
            break
        print("Invalid horse.")
    positions = {h: 0 for h in horses}
    finish = 20
    while True:
        clear_screen()
        for h in horses:
            track = "." * positions[h] + h
            print(track)
        time.sleep(0.2)
        for h in horses:
            positions[h] += random.randint(1, 3)
        if max(positions.values()) >= finish:
            break
    winner = max(positions, key=positions.get)
    print(f"Winner: {winner}")
    wallet -= bet
    if pick == winner:
        winnings = bet * 2
        wallet += winnings
        print(f"Your horse won! You gain {winnings}$.")
    else:
        print(f"Your horse lost. You lose {bet}$.")
    save_wallet(wallet)
    return wallet


def random_spin(wallet: int) -> int:
    print("\n--- RANDOM ---")
    print(f"Wallet: {wallet}$")
    if wallet < 1000:
        print("Need at least 1000$ for a spin.")
        return wallet
    wallet -= 1000
    win = random.random() < 0.5
    if win:
        wallet += 2000
        print("Paid 1000 -> Won 2000 (WIN)")
    else:
        print("Paid 1000 -> Won 0 (LOSE)")
    save_wallet(wallet)
    return wallet


def bank_menu(wallet: int, user_id: str) -> int:
    while True:
        print(f"\n--- Bank ---\nWallet: {wallet}$")
        print("(P) Pay to Fishing")
        print("(Q) Back")
        action = input("Choose: ").strip().upper()
        if action == "P":
            try:
                amount = int(input("Amount to send: "))
            except ValueError:
                print("Invalid amount.")
                continue
            if amount <= 0 or amount > wallet:
                print("Invalid amount.")
                continue
            wallet -= amount
            save_wallet(wallet)
            code = bank.create_transfer(user_id, amount, from_app="casino", to_app="fishing")
            subprocess.Popen([sys.executable, "fishing.py", "--autoclaim", code, "--user", user_id])
            sys.exit(0)
        elif action == "Q":
            break
        else:
            print("Invalid choice.")
    return wallet


def main() -> None:
    args = sys.argv[1:]
    autoclaim_code = None
    autoclaim_user = None
    for i, arg in enumerate(args):
        if arg == "--autoclaim" and i + 1 < len(args):
            autoclaim_code = args[i + 1].upper()
        elif arg == "--user" and i + 1 < len(args):
            autoclaim_user = args[i + 1]

    wallet = load_wallet()
    user_id = autoclaim_user or "player1"

    if autoclaim_code and autoclaim_user:
        try:
            amount, from_app = bank.claim_transfer(autoclaim_code, expect_to_app="casino", user_id=autoclaim_user)
        except Exception as e:
            print(f"Auto-claim failed: {e}")
        else:
            wallet += amount
            save_wallet(wallet)
            print(f"Auto-received ${amount} from {from_app}.")
    while True:
        print(f"\n--- Casino ---\nWallet: {wallet}$")
        print("  1) One or Two")
        print("  2) Horse Race (ASCII)")
        print("  3) RANDOM (1000$ spin)")
        print("  4) Bank (Pay)")
        print("  5) Return to Fishing")
        print("  6) Exit")
        choice = input("Choose: ").strip()
        if choice == "1":
            wallet = one_or_two(wallet)
        elif choice == "2":
            wallet = horse_race(wallet)
        elif choice == "3":
            wallet = random_spin(wallet)
        elif choice == "4":
            wallet = bank_menu(wallet, user_id)
        elif choice == "5":
            save_wallet(wallet)
            subprocess.Popen([sys.executable, "fishing.py"])
            sys.exit(0)
        elif choice == "6":
            save_wallet(wallet)
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()

