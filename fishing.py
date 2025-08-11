# Python translation of the PowerShell Fishing Game
# Console-based fishing game with multiple zones, shop, and save/load system

import json
import math
import os
import random
import time
import sys
import select
import hashlib
import hmac
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
try:
    import curses
except Exception:  # pragma: no cover - curses may be missing on some platforms
    curses = None

if sys.platform == 'win32':
    import msvcrt
else:
    import tty
    import termios

# --------------------------- Utility functions ---------------------------

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Simple ANSI color mapping (no external deps)
COLORS = {
    "DarkGray": "\033[90m",
    "Green": "\033[32m",
    "Magenta": "\033[35m",
    "Cyan": "\033[36m",
    "Yellow": "\033[33m",
    "DarkYellow": "\033[33m",
    "Red": "\033[31m",
    "White": "\033[37m",
    "Reset": "\033[0m",
}

def color_text(text: str, color: str) -> str:
    return f"{COLORS.get(color, COLORS['White'])}{text}{COLORS['Reset']}"

# Season helpers
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
SEASON_EMOJI = {
    "Spring": "🌸",
    "Summer": "☀️",
    "Autumn": "🍂",
    "Winter": "❄️",
}

# Non-blocking keyboard helpers
class RawInput:
    def __enter__(self):
        if sys.platform != 'win32':
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if sys.platform != 'win32':
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

def key_pressed():
    if sys.platform == 'win32':
        return msvcrt.kbhit()
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr != []

def read_key():
    if sys.platform == 'win32':
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):
            msvcrt.getwch()
            return ''
        return ch
    return sys.stdin.read(1)

ENTER_KEYS = ('\r', '\n', '\r\n', '\x0d')

# Secret key for save file signature
SAVE_SIGNATURE_KEY = os.environ.get('SAVE_SIGNATURE_KEY', 'default_save_signature_key')


def compute_save_signature(data: Dict) -> str:
    """Compute HMAC-SHA256 signature for given data using canonical JSON."""
    serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
    key = SAVE_SIGNATURE_KEY.encode('utf-8')
    return hmac.new(key, serialized.encode('utf-8'), hashlib.sha256).hexdigest()

# [FISH_TRAP HELPERS]

def format_remaining_time(seconds: float) -> str:
    """Return human readable H:M:S string for given seconds."""
    if seconds <= 0:
        return "0s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s or not parts:
        parts.append(f"{s}s")
    return " ".join(parts)

# Boss spawn chance configuration
BASE_BOSS_CHANCE = 0.10  # existing base chance (10%)
BOSS_BONUS_PER_STREAK = 0.005  # additional 0.5% per streak
BOSS_CHANCE_CAP = 0.20  # maximum 20% chance

# Floating Island appearance chance
FLOATING_ISLAND_DAILY_CHANCE = 0.30

# --------------------------- Fish data ---------------------------

FISH_LAKE = [
    {"name": "Carp", "rarity": "Common", "price": 1, "xp": 5, "seasons": ["Spring", "Summer"]},
    {"name": "Tilapia", "rarity": "Common", "price": 1.25, "xp": 5},
    {"name": "Grass carp", "rarity": "Uncommon", "price": 5, "xp": 7},
    {"name": "Catfish", "rarity": "Rare", "price": 10, "xp": 10, "time_of_day": ["Night"]},
    {"name": "Snakehead fish", "rarity": "Legendary", "price": 50, "xp": 50},
    {"name": "Bluegill", "rarity": "Common", "price": 3, "xp": 5, "time_of_day": ["Day"]},
    {"name": "Northern Pike", "rarity": "Uncommon", "price": 12, "xp": 15},
    {"name": "Largemouth Bass", "rarity": "Common", "price": 8, "xp": 10},
    {"name": "Rainbow Trout", "rarity": "Uncommon", "price": 15, "xp": 12, "time_of_day": ["Day"]},
    {"name": "Yellow Perch", "rarity": "Common", "price": 5, "xp": 7, "seasons": ["Autumn", "Winter"]},
    {"name": "Muskellunge", "rarity": "Legendary", "price": 40, "xp": 35, "seasons": ["Summer"]},
    {"name": "Walleye", "rarity": "Common", "price": 7, "xp": 9},
    {"name": "Lake Sturgeon", "rarity": "Rare", "price": 20, "xp": 25},
    {"name": "White Bass", "rarity": "Uncommon", "price": 6, "xp": 8},
    {"name": "Channel Catfish", "rarity": "Rare", "price": 18, "xp": 20},
]

FISH_SEA = [
    {"name": "Starfish", "rarity": "Uncommon", "base_price": 1.25, "xp": 7},
    {"name": "Tuna", "rarity": "Rare", "base_price": 2, "xp": 10},
    {"name": "Shark", "rarity": "Rare", "base_price": 7, "xp": 10},
    {"name": "Whale", "rarity": "Legendary", "base_price": 5, "xp": 50},
    {"name": "Flying Fish", "rarity": "Uncommon", "base_price": 2.5, "xp": 10},
    {"name": "Swordfish", "rarity": "Rare", "base_price": 18, "xp": 30},
    {"name": "Electric Eel", "rarity": "Rare", "base_price": 22, "xp": 30},
    {"name": "Lionfish", "rarity": "Epic", "base_price": 35, "xp": 100},
    {"name": "Giant Blue Marlin", "rarity": "Legendary", "base_price": 55, "xp": 1000},
    {"name": "Sunfish", "rarity": "Mythical", "base_price": 70, "xp": 1000},
    {"name": "Dolphin", "rarity": "Uncommon", "base_price": 15, "xp": 20},
    {"name": "Barracuda", "rarity": "Rare", "base_price": 30, "xp": 40},
    {"name": "Clownfish", "rarity": "Common", "base_price": 6, "xp": 8},
    {"name": "Mahi-Mahi", "rarity": "Rare", "base_price": 25, "xp": 30},
    {"name": "Blue Marlin", "rarity": "Legendary", "base_price": 90, "xp": 100},
    {"name": "Kingfish", "rarity": "Uncommon", "base_price": 18, "xp": 22},
    {"name": "Emperor Angelfish", "rarity": "Rare", "base_price": 35, "xp": 45},
    {"name": "Grouper", "rarity": "Uncommon", "base_price": 12, "xp": 16},
    {"name": "Triggerfish", "rarity": "Rare", "base_price": 20, "xp": 25},
    {"name": "Napoleon Wrasse", "rarity": "Legendary", "base_price": 60, "xp": 80},
]

FISH_BATHYAL = [
    {"name": "Deep-sea Dragonfish", "rarity": "Rare", "base_price": 35, "xp": 45},
    {"name": "Lanternfish", "rarity": "Uncommon", "base_price": 15, "xp": 18},
    {"name": "Anglerfish", "rarity": "Uncommon", "base_price": 20, "xp": 25},
    {"name": "Black Swallower", "rarity": "Legendary", "base_price": 90, "xp": 120},
    {"name": "Goblin Shark", "rarity": "Legendary", "base_price": 50, "xp": 70},
    {"name": "Cusk Eel", "rarity": "Rare", "base_price": 25, "xp": 30},
    {"name": "Viperfish", "rarity": "Rare", "base_price": 30, "xp": 40},
    {"name": "Giant Squid", "rarity": "Legendary", "base_price": 80, "xp": 100},
    {"name": "Brilliant Lanternfish", "rarity": "Rare", "base_price": 18, "xp": 22},
    {"name": "Swallowtail", "rarity": "Uncommon", "base_price": 12, "xp": 15},
]

FISH_ABYSS_TRENCH = [
    {"name": "Lanternfish", "rarity": "Common", "price": 15},
    {"name": "Angler Leviathan", "rarity": "Legendary", "price": 100, "xp": 150},
    {"name": "Giant Squid", "rarity": "Legendary", "price": 75, "xp": 100},
    {"name": "Ancient Key", "rarity": "Legendary", "price": 25},
    {"name": "Abyssal Octopus", "rarity": "Rare", "price": 50, "xp": 60},
    {"name": "Cusk Eel", "rarity": "Rare", "price": 40, "xp": 50},
    {"name": "Black Swallower", "rarity": "Legendary", "price": 80, "xp": 120},
    {"name": "Abyssal Dragonfish", "rarity": "Rare", "price": 60, "xp": 70},
    {"name": "Swallower Eel", "rarity": "Rare", "price": 50, "xp": 60},
    {"name": "Abyssal Squid", "rarity": "Rare", "price": 70, "xp": 80},
    {"name": "Giant Anglerfish", "rarity": "Legendary", "price": 100, "xp": 130},
    {"name": "Benthic Eel", "rarity": "Uncommon", "price": 30, "xp": 40},
    {"name": "Abyssal Leviathan", "rarity": "Legendary", "price": 200, "xp": 350},
    {"name": "Trench Dragonfish", "rarity": "Rare", "price": 80, "xp": 120},
    {"name": "Bioluminescent Squid", "rarity": "Rare", "price": 50, "xp": 75},
    {"name": "Ghost Shark", "rarity": "Legendary", "price": 150, "xp": 200},
    {"name": "Colossal Squid", "rarity": "Mythical", "price": 250, "xp": 400},
    {"name": "Abyssal Angler", "rarity": "Legendary", "price": 175, "xp": 250},
    {"name": "Barreleye Fish", "rarity": "Rare", "price": 40, "xp": 55},
    {"name": "Abyssal Cusk Eel", "rarity": "Common", "price": 20, "xp": 30},
    {"name": "Abyssal Lanternfish", "rarity": "Uncommon", "price": 25, "xp": 40},
    {"name": "Giant Fangtooth", "rarity": "Legendary", "price": 100, "xp": 150},
]

FISH_ANCIENT_SEA = [
    {"name": "Mosasaurus", "rarity": "Legendary", "price": 350, "xp": 500},
    {"name": "Dunkleosteus", "rarity": "Mythical", "price": 500, "xp": 700},
    {"name": "Megalodon", "rarity": "Mythical", "price": 1000, "xp": 1500},
    {"name": "Leedsichthys", "rarity": "Exotic", "price": 250, "xp": 300},
    {"name": "Shonisaurus", "rarity": "Legendary", "price": 300, "xp": 400},
    {"name": "Ichthyosaurus", "rarity": "Legendary", "price": 200, "xp": 250},
    {"name": "Tylosaurus", "rarity": "Legendary", "price": 250, "xp": 300},
    {"name": "Pliosaurus", "rarity": "Legendary", "price": 350, "xp": 500},
    {"name": "Tyrannosaurus Rex", "rarity": "Mythical", "price": 600, "xp": 800},
    {"name": "Sharksaurus", "rarity": "Legendary", "price": 450, "xp": 600},
    {"name": "Acanthodes", "rarity": "Exotic", "price": 300, "xp": 350},
]

FISH_MYSTIC_SPRING = [
    {"name": "Prism Trout", "rarity": "Rare", "price": 15, "xp": 10},
    {"name": "Spirit Koi", "rarity": "Epic", "price": 25, "xp": 25},
    {"name": "Phoenix Scale Carp", "rarity": "Mythical", "price": 50, "xp": 40},
    {"name": "Moonlit Koi", "rarity": "Mythical", "price": 100, "xp": 150},
    {"name": "Water Sprite", "rarity": "Epic", "price": 75, "xp": 100},
    {"name": "Crystal Trout", "rarity": "Legendary", "price": 120, "xp": 200},
    {"name": "Spirit Nymph", "rarity": "Epic", "price": 90, "xp": 120},
    {"name": "Water Dragonfish", "rarity": "Rare", "price": 45, "xp": 60},
    {"name": "Moonbeam Bass", "rarity": "Rare", "price": 40, "xp": 50},
    {"name": "Mystic Swallower", "rarity": "Legendary", "price": 150, "xp": 250},
    {"name": "Luminous Catfish", "rarity": "Uncommon", "price": 25, "xp": 35},
    {"name": "Frostfin Koi", "rarity": "Rare", "price": 50, "xp": 70},
    {"name": "Glimmering Angelfish", "rarity": "Epic", "price": 60, "xp": 80},
]

FISH_FLOATING_ISLAND = [
    {"name": "Cloud Carp", "rarity": "Uncommon", "price": 35, "xp": 40},
    {"name": "Sky Ray", "rarity": "Rare", "price": 90, "xp": 110},
    {"name": "Aurora Koi", "rarity": "Epic", "price": 140, "xp": 170},
    {"name": "Zephyr Tuna", "rarity": "Rare", "price": 110, "xp": 130},
    {"name": "Aether Squid", "rarity": "Epic", "price": 160, "xp": 200},
    {"name": "Radiant Sunfish", "rarity": "Legendary", "price": 240, "xp": 280},
    {"name": "Nimbus Marlin", "rarity": "Legendary", "price": 210, "xp": 260},
    {"name": "Celestial Marlin", "rarity": "Mythical", "price": 320, "xp": 380},
]

# Boss definitions for each zone
ZONE_BOSS_MAP = {
    "Lake": {
        "name": "The Drowned King",
        "warning": "🧱 The water trembles... The Drowned King is near!",
    },
    "Sea": {
        "name": "Kraken",
        "warning": "🌊 Tentacles rise! The Kraken is attacking!",
    },
    "Bathyal": {
        "name": "Ancient Leviathan",
        "warning": "🐉 A massive shadow looms... Leviathan emerges!",
    },
    "Mystic Spring": {
        "name": "Mystic Dragonfish",
        "warning": "✨ The water glows... A Mystic Dragonfish reveals itself!",
    },
    "Abyss Trench": {
        "name": "Abyss King",
        "warning": "🌑 Darkness thickens... The Abyss King awakens!",
    },
    "Ancient Sea": {
        "name": "Godfish Eternus",
        "warning": "🕯 Time stands still... Godfish Eternus appears!",
    },
    "Floating Island": {
        "name": "Sky Serpent Sovereign",
        "warning": "🌪 The winds roar... The Sky Serpent descends!",
    },
}

# Inject boss fish into zone fish lists
FISH_LAKE.append({"name": ZONE_BOSS_MAP["Lake"]["name"], "rarity": "???", "price": 1000, "xp": 6000})
FISH_SEA.append({"name": ZONE_BOSS_MAP["Sea"]["name"], "rarity": "???", "base_price": 1000, "xp": 7000})
FISH_BATHYAL.append({"name": ZONE_BOSS_MAP["Bathyal"]["name"], "rarity": "???", "base_price": 1000, "xp": 8000})
FISH_MYSTIC_SPRING.append({"name": ZONE_BOSS_MAP["Mystic Spring"]["name"], "rarity": "???", "price": 1000, "xp": 9000})
FISH_ABYSS_TRENCH.append({"name": ZONE_BOSS_MAP["Abyss Trench"]["name"], "rarity": "???", "price": 1000, "xp": 9500})
FISH_ANCIENT_SEA.append({"name": ZONE_BOSS_MAP["Ancient Sea"]["name"], "rarity": "???", "price": 1000, "xp": 10000})
FISH_FLOATING_ISLAND.append({
    "name": ZONE_BOSS_MAP["Floating Island"]["name"],
    "rarity": "???",
    "price": 1200,
    "xp": 8500,
})

# Map zones to their fish lists for easy lookup throughout the game
ZONE_FISH_MAP = {
    "Lake": FISH_LAKE,
    "Sea": FISH_SEA,
    "Bathyal": FISH_BATHYAL,
    "Mystic Spring": FISH_MYSTIC_SPRING,
    "Abyss Trench": FISH_ABYSS_TRENCH,
    "Ancient Sea": FISH_ANCIENT_SEA,
    "Floating Island": FISH_FLOATING_ISLAND,
}

# Base reward values per rarity used for quest reward calculation
RARITY_BASE_REWARD = {
    "Common": 10,
    "Uncommon": 20,
    "Rare": 40,
    "Epic": 80,
    "Legendary": 160,
    "Mythical": 320,
    "Exotic": 640,
}

EXOTIC_FISH_FULL_MOON = [
    {"name": "Phantom Shark", "rarity": "Exotic", "price": 100, "xp": 1000},
    {"name": "Shadowfin", "rarity": "Exotic", "price": 100, "xp": 1000},
    {"name": "Abyssal Ghost", "rarity": "Exotic", "price": 100, "xp": 1000},
]

SEA_PRICE_MULTIPLIER = {
    "Uncommon": 1.25,
    "Rare": 2,
    "Epic": 3,
    "Legendary": 5,
    "Mythical": 7,
}

SHOP_ITEMS = [
    {"name": "Boat", "price": 25000, "description": "Access Sea zone"},
    {"name": "Submarine", "price": 1000000, "description": "Access Bathyal zone"},
    {"name": "Torch", "price": 5000, "description": "Access Mystic Spring zone"},
    {"name": "Submarine Upgrade 01", "price": 10000000, "description": "Access Abyss Trench zone"},
    {"name": "Submarine Upgrade 02", "price": 100000000, "description": "Access Ancient Sea zone"},
]

DAILY_EVENT_EFFECTS = {
    "Double XP Day": "XP x2",
    "Treasure Hunt": "10% chest",
    "Speedy Fisher": "Easier minigame",
    "Exotic Surge": "Exotic anywhere",
    "Jackpot Sell": "5% sale x3",
    "Streak Madness": "+5% rare/streak",
    "Full Moon Night": "Exotic+Boss boosted",
}

# [FISH_TRAP CONSTANTS]
REAL_SECONDS_PER_INGAME_DAY = 60 * 60 * 24
TRAP_OVERDUE_SECONDS = 60 * 60 * 12
TRAP_MAX_ACTIVE = 10
TRAP_CAPACITY_MAX = 50

BAIT_PRICES = {
    "trap": 1500,
    "normal": 1000,
    "advanced": 5000,
    "expert": 100000,
    "legend": 1500000,
}

BAIT_RARITY_MAP = {
    "normal": ["Common", "Uncommon"],
    "advanced": ["Rare", "Epic"],
    "expert": ["Legendary", "Mythical"],
    "legend": ["Exotic", "???"],
}

@dataclass
class Quest:
    """Represents a quest tied to a specific zone."""

    quest_type: int  # 1: specific fish, 2: rarity
    zone: str
    target_fish: str | None = None
    rarity: str | None = None
    amount: int = 1
    progress: int = 0
    reward: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)

    def is_completed(self) -> bool:
        return self.progress >= self.amount


class QuestManager:
    """Manages quests for all zones."""

    def __init__(self, quests_data: Dict[str, List[Dict]] | None = None):
        self.zone_quests: Dict[str, List[Quest]] = {}
        self.original_amounts: Dict[str, List[int]] = {}
        self.quest_boost_active = False
        # Initialize quests from saved data if provided
        if quests_data:
            for zone, quests in quests_data.items():
                self.zone_quests[zone] = []
                self.original_amounts[zone] = []
                for q in quests:
                    quest = Quest(**q)
                    self.zone_quests[zone].append(quest)
                    self.original_amounts[zone].append(q.get('amount', quest.amount))
                    if quest.reward == 0:
                        rarity = quest.rarity
                        if quest.quest_type == 1 and not rarity:
                            fish_list = ZONE_FISH_MAP.get(zone, [])
                            for f in fish_list:
                                if f["name"] == quest.target_fish:
                                    rarity = f["rarity"]
                                    quest.rarity = rarity
                                    break
                        base = RARITY_BASE_REWARD.get(rarity, 10)
                        quest.reward = base * quest.amount
        # Ensure every zone has a quest list
        for zone in ZONE_FISH_MAP.keys():
            self.zone_quests.setdefault(zone, [])
            self.original_amounts.setdefault(zone, [])
            # Trim excess quests and fill up to 10
            self.zone_quests[zone] = self.zone_quests[zone][:10]
            self.original_amounts[zone] = self.original_amounts[zone][:10]
            while len(self.zone_quests[zone]) < 10:
                quest = self.generate_quest(zone)
                self.zone_quests[zone].append(quest)
        
    def to_dict(self) -> Dict[str, List[Dict]]:
        return {zone: [q.to_dict() for q in quests] for zone, quests in self.zone_quests.items()}

    def to_save_dict(self) -> Dict[str, List[Dict]]:
        data: Dict[str, List[Dict]] = {}
        for zone, quests in self.zone_quests.items():
            zone_list: List[Dict] = []
            for i, q in enumerate(quests):
                q_data = q.to_dict()
                if zone in self.original_amounts and i < len(self.original_amounts[zone]):
                    q_data['amount'] = self.original_amounts[zone][i]
                zone_list.append(q_data)
            data[zone] = zone_list
        return data

    def get_quests_for_zone(self, zone_name: str) -> List[Quest]:
        return self.zone_quests.get(zone_name, [])

    def generate_quest(self, zone: str) -> Quest:
        fish_list = [
            f for f in ZONE_FISH_MAP.get(zone, [])
            if f.get("rarity") not in ("???", "Exotic")
        ]
        if not fish_list:
            return Quest(1, zone, target_fish="Carp", amount=1, reward=10)
        quest_type = random.choice([1, 2])
        amount = random.randint(1, 20)
        if quest_type == 1:
            fish = random.choice(fish_list)
            rarity = fish["rarity"]
            target_fish = fish["name"]
        else:
            rarity = random.choice(list({f["rarity"] for f in fish_list}))
            target_fish = None

        max_amount = 15
        if rarity == "Legendary":
            max_amount = 5
        elif rarity == "Boss":
            max_amount = 1
        amount = min(amount, max_amount)

        base_values = {
            "Common": 10,
            "Uncommon": 20,
            "Rare": 100,
            "Epic": 175,
            "Mythical": 200,
            "Legendary": 500,
            "Boss": 10000,
        }
        reward = base_values.get(rarity, 0) * amount
        if self.quest_boost_active:
            adjusted_amount = max(1, math.ceil(amount * 0.7))
        else:
            adjusted_amount = amount
        quest = Quest(
            quest_type,
            zone,
            target_fish=target_fish,
            rarity=rarity,
            amount=adjusted_amount,
            reward=reward,
        )
        self.original_amounts.setdefault(zone, []).append(amount)
        return quest

    def apply_quest_boost(self):
        self.quest_boost_active = True
        for zone, quests in self.zone_quests.items():
            self.original_amounts.setdefault(zone, [])
            for i, q in enumerate(quests):
                if len(self.original_amounts[zone]) <= i:
                    self.original_amounts[zone].append(q.amount)
                orig = self.original_amounts[zone][i]
                q.amount = max(1, math.ceil(orig * 0.7))

    def finish_quest(self, zone: str, quest_index: int) -> int:
        quests = self.get_quests_for_zone(zone)
        if quest_index < 0 or quest_index >= len(quests):
            return 0
        quest = quests[quest_index]
        if not quest.is_completed():
            return 0
        reward = quest.reward
        new_quest = self.generate_quest(zone)
        quests[quest_index] = new_quest
        if zone in self.original_amounts:
            new_orig = self.original_amounts[zone].pop()
            if len(self.original_amounts[zone]) <= quest_index:
                self.original_amounts[zone].append(new_orig)
            else:
                self.original_amounts[zone][quest_index] = new_orig
        return reward

    def show_quests_for_zone(self, zone_name: str):
        quests = self.get_quests_for_zone(zone_name)
        if not quests:
            print("No quests available here.")
            return
        print("Available quests:")
        for q in quests:
            if q.quest_type == 1:
                desc = f"Catch {q.amount} {q.target_fish}"
            else:
                desc = f"Catch {q.amount} {q.rarity} fish"
            status = f"{q.progress}/{q.amount}"
            print(f"- {desc} ({status})")

    def show_all_quests(self):
        for zone, quests in self.zone_quests.items():
            print(f"== {zone} ==")
            for q in quests:
                if q.quest_type == 1:
                    desc = f"Catch {q.amount} {q.target_fish}"
                else:
                    desc = f"Catch {q.amount} {q.rarity} fish"
                print(f"{desc} - {q.progress}/{q.amount}")

    def update_quest_progress(self, player_zone: str, fish_name: str, rarity: str):
        for q in self.get_quests_for_zone(player_zone):
            if q.quest_type == 1 and q.target_fish == fish_name and q.progress < q.amount:
                q.progress += 1
                print(f"Quest update: {q.target_fish} {q.progress}/{q.amount}")
            elif q.quest_type == 2 and q.rarity == rarity and q.progress < q.amount:
                q.progress += 1
                print(f"Quest update: {q.rarity} fish {q.progress}/{q.amount}")


# --------------------------- Game Class ---------------------------

class Game:
    def __init__(self):
        self.save_file = os.path.join(os.getcwd(), 'save_data.json')
        # default values
        self.balance = 100
        self.inventory: List[Dict] = []
        self.has_submarine = False
        self.has_boat = False
        self.has_torch = False
        self.has_abyss_trench_access = False
        self.has_ancient_sea_access = False
        self.has_ancient_key = False
        self.has_floating_key = False
        self.current_hour = 0
        self.current_day = 0
        self.floating_island_day = self.current_day
        self.floating_island_today = False
        self.floating_island_visible = False
        self.event = "Nothing"
        self.level = 0
        self.xp = 0
        self.streak = 0
        self.discovery: Dict[str, Dict] = {}
        self.current_zone = "Lake"
        self.current_fish_list = FISH_LAKE
        self.current_zone_catch_length = 5
        self.current_fish = None
        self.fast_fishing_price = 15  # base cost per extra fish
        self.loaded_quests: Dict[str, List[Dict]] = {}
        self.daily_event: Optional[str] = None
        self.daily_event_day: int = self.current_day
        # [FISH_TRAP fields]
        self.inventory_fish_traps = 0
        self.baits = {"normal": 0, "advanced": 0, "expert": 0, "legend": 0}
        self.active_traps: List[Dict] = []
        # load existing data if any
        self.load_game()
        self.quest_manager = QuestManager(self.loaded_quests)
        self.update_floating_island_state()
        self.roll_daily_event_if_needed()

    # -------------- Save & Load --------------
    def save_game(self):
        data = {
            'balance': self.balance,
            'inventoryFish': self.inventory,
            'hasSubmarine': self.has_submarine,
            'hasBoat': self.has_boat,
            'hasTorch': self.has_torch,
            'hasAbyssTrenchAccess': self.has_abyss_trench_access,
              'hasAncientSeaAccess': self.has_ancient_sea_access,
              'hasAncientKey': self.has_ancient_key,
              'hasFloatingKey': self.has_floating_key,
              'floatingIslandDay': self.floating_island_day,
              'floatingIslandToday': self.floating_island_today,
              'floatingIslandVisible': self.floating_island_visible,
              'currentHour': self.current_hour,
              'currentDay': self.current_day,
              'event': self.event,
              'level': self.level,
              'xp': self.xp,
            'discovery': self.discovery,
            'quests': self.quest_manager.to_save_dict(),
            'streak': self.streak,
            'fastFishingPrice': self.fast_fishing_price,
            'dailyEvent': self.daily_event,
            'dailyEventDay': self.daily_event_day,
            'inventoryFishTraps': self.inventory_fish_traps,
            'baits': self.baits,
            'activeTraps': self.active_traps,
        }
        data_to_sign = data.copy()
        data['sig'] = compute_save_signature(data_to_sign)
        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_game(self):
        if os.path.exists(self.save_file):
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            saved_sig = data.pop('sig', '')
            computed_sig = compute_save_signature(data)
            if saved_sig != computed_sig:
                print("⚠️ Save file appears to have been tampered with (bad signature).")
                exit()
            self.balance = data.get('balance', 100)
            self.inventory = data.get('inventoryFish', [])
            self.has_submarine = data.get('hasSubmarine', False)
            self.has_boat = data.get('hasBoat', False)
            self.has_torch = data.get('hasTorch', False)
            self.has_abyss_trench_access = data.get('hasAbyssTrenchAccess', False)
            self.has_ancient_sea_access = data.get('hasAncientSeaAccess', False)
            self.has_ancient_key = data.get('hasAncientKey', False)
            self.has_floating_key = data.get('hasFloatingKey', False)
            self.current_hour = data.get('currentHour', 0)
            self.current_day = data.get('currentDay', 0)
            self.floating_island_day = data.get('floatingIslandDay', self.current_day)
            self.floating_island_today = data.get('floatingIslandToday', False)
            self.floating_island_visible = data.get('floatingIslandVisible', False)
            self.event = data.get('event', 'Nothing')
            self.level = data.get('level', 0)
            self.xp = data.get('xp', 0)
            self.streak = data.get('streak', 0)
            self.fast_fishing_price = data.get('fastFishingPrice', 15)
            self.daily_event = data.get('dailyEvent', None)
            self.daily_event_day = data.get('dailyEventDay', self.current_day)
            self.discovery = data.get('discovery', {})
            self.loaded_quests = data.get('quests', {})
            self.inventory_fish_traps = data.get('inventoryFishTraps', 0)
            self.baits = data.get('baits', {"normal": 0, "advanced": 0, "expert": 0, "legend": 0})
            self.active_traps = data.get('activeTraps', [])
        else:
            # defaults already set
            self.loaded_quests = {}

    def roll_daily_event_if_needed(self):
        if self.daily_event_day != self.current_day:
            self.daily_event_day = self.current_day
            candidates = [
                "Double XP Day",
                "Treasure Hunt",
                "Speedy Fisher",
                "Exotic Surge",
                "Jackpot Sell",
                "Streak Madness",
            ]
            if self.event == "Full Moon":
                candidates.append("Full Moon Night")
            if random.random() < 0.30:
                self.daily_event = random.choice(candidates)
            else:
                self.daily_event = None
            self.save_game()

    def update_floating_island_state(self):
        prev_day = self.floating_island_day
        prev_today = self.floating_island_today
        prev_visible = self.floating_island_visible
        if self.floating_island_day != self.current_day:
            self.floating_island_day = self.current_day
            self.floating_island_today = (
                self.has_floating_key and random.random() < FLOATING_ISLAND_DAILY_CHANCE
            )
        self.floating_island_visible = (
            self.floating_island_today and 12 <= self.current_hour <= 16
        )
        if self.floating_island_visible and self.current_hour == 12 and not prev_visible:
            print("☁️ The Floating Island emerges (12–16h)!")
        if self.current_zone == "Floating Island" and self.current_hour > 16:
            safe_zone = "Sea" if "Sea" in self.get_unlocked_zones() else "Lake"
            self.current_zone = safe_zone
            self.current_fish_list = self.get_fish_list_for_zone(safe_zone)
            self.current_zone_catch_length = 3 if safe_zone == "Sea" else 5
            print("☁️ The Floating Island fades away. You return to the waters below.")
        if (
            prev_day != self.floating_island_day
            or prev_today != self.floating_island_today
            or prev_visible != self.floating_island_visible
        ):
            self.save_game()

    # -------------- Level & XP --------------
    def calculate_xp_for_level(self, level: int) -> int:
        if level == 0:
            return 100
        return 100 + (level * 100)

    def check_level_up(self):
        xp_needed = self.calculate_xp_for_level(self.level)
        while self.xp >= xp_needed and self.level < 100:
            self.xp -= xp_needed
            self.level += 1
            if self.level >= 100:
                self.level = 100
                self.xp = 0
                print("Congratulations! You reached max level 100!")
                return
            else:
                print(f"Congratulations! You leveled up to level {self.level}!")
            xp_needed = self.calculate_xp_for_level(self.level)
        if self.level >= 100:
            self.xp = 0

    # -------------- Rarity helpers --------------
    def get_rarity_color(self, rarity: str) -> str:
        mapping = {
            "Common": "DarkGray",
            "Uncommon": "Green",
            "Rare": "Magenta",
            "Epic": "Cyan",
            "Legendary": "Yellow",
            "Mythical": "DarkYellow",
            "Exotic": "Red",
            "???": "Red",
        }
        return mapping.get(rarity, "White")

    def get_xp_by_rarity(self, rarity: str) -> int:
        values = {
            "Common": 5,
            "Uncommon": 10,
            "Rare": 30,
            "Epic": 100,
            "Legendary": 1000,
            "Mythical": 1000,
            "Exotic": 100000,
        }
        return values.get(rarity, 0)

    # -------------- Zone helpers --------------
    def get_unlocked_zones(self) -> List[str]:
        zones = ["Lake"]
        if self.has_boat:
            zones.append("Sea")
        if self.has_submarine:
            zones.append("Bathyal")
        if self.has_torch:
            zones.append("Mystic Spring")
        if self.has_abyss_trench_access:
            zones.append("Abyss Trench")
        if self.has_ancient_sea_access:
            zones.append("Ancient Sea")
        if self.has_floating_key and self.floating_island_visible:
            zones.append("Floating Island")
        return zones

    def get_fish_list_for_zone(self, zone: str) -> List[Dict]:
        return ZONE_FISH_MAP.get(zone, FISH_LAKE)

    def get_speed(self) -> float:
        speed = 0.1  # seconds
        if self.current_zone in ("Sea", "Mystic Spring"):
            speed = max(speed / 2, 0.01)
        elif self.current_zone == "Bathyal":
            speed = max(speed / 4, 0.01)
        elif self.current_zone == "Abyss Trench":
            speed = max(speed / 7, 0.01)
        elif self.current_zone == "Ancient Sea":
            speed = max(speed / 10, 0.01)
        elif self.current_zone == "Floating Island":
            speed = max(speed / 12, 0.005)
        return speed

    # -------------- Discovery --------------
    def update_discovery(self, zone: str, fish_name: str, weight: float, value: float):
        zone_data = self.discovery.setdefault(zone, {})
        entry = zone_data.setdefault(fish_name, {
            'count': 0,
            'maxWeight': 0,
            'maxValue': 0,
        })
        entry['count'] += 1
        if weight > entry['maxWeight']:
            entry['maxWeight'] = weight
        if value > entry['maxValue']:
            entry['maxValue'] = value
        zone_data[fish_name] = entry
        self.discovery[zone] = zone_data

    # -------------- Boss minigame --------------
    def run_boss_minigame_rounds(self, rounds: int = 5, zone_len: int = 3, speed: float = 0.02) -> bool:
        bar = "--------------------------"
        margin = 1
        for _ in range(rounds):
            target_start = random.randint(5, len(bar) - zone_len - 1)
            target_end = target_start + zone_len - 1
            extended_start = max(0, target_start - margin)
            extended_end = min(len(bar) - 1, target_end + margin)
            with RawInput():
                prev_i = -1
                for i in range(len(bar)):
                    clear_screen()
                    before = bar[:i]
                    after = bar[i + 1:]
                    line = before + "|" + after
                    target_line = ''.join('=' if target_start <= j <= target_end else ' ' for j in range(len(bar)))
                    print("Boss battle!")
                    print(line)
                    print(target_line)
                    time.sleep(speed)
                    if key_pressed():
                        ch = read_key()
                        if ch == ' ':
                            in_zone = (extended_start <= i <= extended_end) or (
                                prev_i >= 0 and extended_start <= prev_i <= extended_end
                            )
                            if in_zone:
                                break
                    prev_i = i
                else:
                    print("\n>> Time's up! The boss escaped! <<")
                    return False
        return True

    # -------------- Fish generation --------------
    def get_fish_by_weighted_random(self, fish_list: List[Dict], fast_mode: bool = False) -> Dict | None:
        # Chance to encounter zone boss
        boss_chance = BASE_BOSS_CHANCE
        if not fast_mode:
            boss_chance += self.streak * BOSS_BONUS_PER_STREAK
            if self.daily_event == "Full Moon Night":
                boss_chance += 0.10
            boss_chance = min(boss_chance, BOSS_CHANCE_CAP)
            bonus = boss_chance - BASE_BOSS_CHANCE
            if bonus > 0:
                print(f"Boss spawn chance boosted by {bonus*100:.1f}%")
        if random.random() < boss_chance and self.current_zone in ZONE_BOSS_MAP:
            boss = ZONE_BOSS_MAP[self.current_zone]
            print(boss["warning"])
            if self.current_zone == "Floating Island":
                success = self.run_boss_minigame_rounds(rounds=6, zone_len=2, speed=0.015)
            else:
                success = self.run_boss_minigame_rounds()
            if success:
                weight = random.randint(1000, 10000)
                boss_entry = next((f for f in fish_list if f["name"] == boss["name"]), {})
                boss_xp = boss_entry.get("xp", 0)
                boss_price = boss_entry.get("price", 1000)
                xp_gain = boss_xp
                if self.daily_event == "Double XP Day":
                    xp_gain *= 2
                caught = {
                    "name": boss["name"],
                    "rarity": "???",
                    "price": boss_price,
                    "weight": weight,
                    "zone": self.current_zone,
                }
                self.current_fish = caught.copy()
                self.inventory.append(self.current_fish.copy())
                self.xp += xp_gain
                self.check_level_up()
                if self.daily_event == "Treasure Hunt" and random.random() < 0.10:
                    bonus_money = random.randint(500, 2000)
                    self.balance += bonus_money
                    print(f"💰 Treasure Hunt! You found {bonus_money}$!")
                color = self.get_rarity_color("???")
                print("\n" + color_text(f">> You caught {boss['name']} [???] - {weight} kg!", color))
                value = round(weight * boss_price, 2)
                self.update_discovery(self.current_zone, boss["name"], weight, value)
                self.quest_manager.update_quest_progress(self.current_zone, boss["name"], "???")
                self.save_game()
                input("Press Enter to continue...")
            else:
                print("\n>> The boss escaped! <<")
                input("Press Enter to continue...")
            return None
        time_of_day = self.get_time_of_day()
        season = self.get_current_season()
        filtered: List[Dict] = []
        for fish in fish_list:
            if fish.get('rarity') == '???':
                continue
            allowed_times = fish.get('time_of_day')
            allowed_seasons = fish.get('seasons')
            if allowed_times and time_of_day not in allowed_times:
                continue
            if allowed_seasons and season not in allowed_seasons:
                continue
            filtered.append(fish)
        if not filtered:
            filtered = fish_list
        weights = {
            'Common': 5,
            'Uncommon': 3,
            'Rare': 2,
            'Epic': 1,
            'Legendary': 1,
            'Mythical': 1,
            'Exotic': 1 if self.daily_event in ("Exotic Surge", "Full Moon Night") else 0,
        }
        rare_types = {'Rare', 'Epic', 'Legendary', 'Mythical'}
        if self.daily_event in ("Exotic Surge", "Full Moon Night"):
            rare_types.add('Exotic')
        rare_weighted = []
        common_weighted = []
        for fish in filtered:
            rarity = fish.get('rarity', 'Common')
            weight = weights.get(rarity, 3)
            if rarity in rare_types:
                rare_weighted.extend([fish] * weight)
            else:
                common_weighted.extend([fish] * weight)
        if not rare_weighted:
            pool = common_weighted or filtered
            return random.choice(pool)
        total_weight = len(rare_weighted) + len(common_weighted)
        base_chance = len(rare_weighted) / total_weight * 100
        if self.daily_event == "Streak Madness":
            bonus = min(self.streak * 5, 40)
        else:
            bonus = min(self.streak * 2, 20)
        chance = base_chance + bonus
        chance = min(chance, 100)
        if random.randint(1, 100) <= chance:
            pool = rare_weighted
        else:
            pool = common_weighted
        return random.choice(pool)

    def generate_weight(self, name: str, rarity: str) -> float:
        if name == "Shark":
            return random.randint(50, 1000)
        if name == "Whale":
            return random.randint(100, 10000)
        if name == "Tuna":
            return random.randint(10, 75)
        if name == "Flying Fish":
            return random.uniform(1, 3)
        if name == "Swordfish":
            return random.randint(100, 300)
        if name == "Electric Eel":
            return random.randint(10, 50)
        if name == "Lionfish":
            return random.uniform(2, 6)
        if name == "Giant Blue Marlin":
            return random.randint(300, 800)
        if name == "Sunfish":
            return random.randint(500, 1500)
        if name == "Deep-sea Dragonfish":
            return random.randint(5, 20)
        if name == "Lanternfish":
            return random.randint(5, 15)
        if name == "Anglerfish":
            return random.randint(10, 25)
        if name == "Black Swallower":
            return random.randint(2, 10)
        if name == "Goblin Shark":
            return random.randint(50, 100)
        if name == "Angler Leviathan":
            return random.randint(15, 100)
        if name == "Giant Squid":
            return random.randint(1000, 5000)
        if name == "Ancient Key":
            return random.randint(100, 500)
        if name == "Mosasaurus" or name == "Dunkleosteus":
            return random.randint(1000, 3000)
        if name == "Megalodon":
            return random.randint(10000, 50000)
        if name == "Leedsichthys":
            return random.randint(100000, 1000000)
        if name == "Prism Trout":
            return random.randint(20, 80)
        if name == "Spirit Koi":
            return random.randint(20, 150)
        if name == "Phoenix Scale Carp":
            return random.randint(100, 300)
        # default by rarity
        if rarity == "Common":
            return random.uniform(0.5, 2.5)
        if rarity == "Uncommon":
            return random.uniform(1.0, 4.0)
        if rarity == "Rare":
            return random.uniform(2.0, 6.0)
        if rarity == "Epic":
            return random.uniform(3.0, 8.0)
        if rarity == "Legendary":
            return random.uniform(5.0, 12.0)
        if rarity == "Mythical":
            return random.uniform(8.0, 20.0)
        return random.uniform(1.0, 3.0)

    # -------------- Zone choosing --------------
    def choose_zone(self):
        clear_screen()
        print("Choose your fishing zone:")
        print("1. Sea (Need Boat)")
        print("2. Lake")
        print("3. Bathyal (Need Submarine)")
        print("4. Mystic Spring (Need Torch)")
        print("5. Abyss Trench (Need Submarine Upgrade 01)")
        print("6. Ancient Sea (Need Submarine Upgrade 02)")
        print("7. Floating Island (Need Floating Key; 12–16h if visible)")
        choice = input("Pick your choice (1-7): ")
        if choice == "1":
            if not self.has_boat:
                print("You don't have a boat to access Sea zone.")
                time.sleep(3)
                return
            self.current_zone = "Sea"
            self.current_fish_list = FISH_SEA
            self.current_zone_catch_length = 3
            print("You chose Sea zone. Catch zone length set to 3.")
        elif choice == "2":
            self.current_zone = "Lake"
            self.current_fish_list = FISH_LAKE
            self.current_zone_catch_length = 5
            print("You chose Lake zone. Catch zone length set to 5.")
        elif choice == "3":
            if not self.has_submarine:
                print("You don't have a submarine to access Bathyal zone.")
                time.sleep(3)
                return
            self.current_zone = "Bathyal"
            self.current_fish_list = FISH_BATHYAL
            self.current_zone_catch_length = 5
            print("You chose Bathyal zone. Minigame speed x4 faster.")
        elif choice == "4":
            if not self.has_torch:
                print("You don't have a Torch to access Mystic Spring.")
                time.sleep(3)
                return
            self.current_zone = "Mystic Spring"
            self.current_fish_list = FISH_MYSTIC_SPRING
            self.current_zone_catch_length = 5
            print("You chose Mystic Spring. Minigame speed x2 faster.")
        elif choice == "5":
            if not self.has_abyss_trench_access:
                print("You don't have Submarine Upgrade 01 to access Abyss Trench.")
                time.sleep(3)
                return
            self.current_zone = "Abyss Trench"
            self.current_fish_list = FISH_ABYSS_TRENCH
            self.current_zone_catch_length = 4
            print("You chose Abyss Trench. Minigame speed x7 faster.")
        elif choice == "6":
            if not self.has_ancient_sea_access:
                print("You don't have access to Ancient Sea.")
                time.sleep(3)
                return
            self.current_zone = "Ancient Sea"
            self.current_fish_list = FISH_ANCIENT_SEA
            self.current_zone_catch_length = 3
            print("You chose Ancient Sea. Minigame speed x10 faster.")
        elif choice == "7":
            if not self.has_floating_key:
                print("You need the FLOATING KEY.")
                time.sleep(3)
                return
            if not self.floating_island_visible:
                print("The Floating Island is not visible right now (12–16h only).")
                time.sleep(3)
                return
            self.current_zone = "Floating Island"
            self.current_fish_list = FISH_FLOATING_ISLAND
            self.current_zone_catch_length = 2
            print("You reached the Floating Island. Minigame is much harder!")
        else:
            print("Invalid choice, defaulting to Lake.")
            self.current_zone = "Lake"
            self.current_fish_list = FISH_LAKE
            self.current_zone_catch_length = 5
            time.sleep(2)
        self.quest_manager.show_quests_for_zone(self.current_zone)
        time.sleep(2)

    # -------------- Time & Events --------------
    def get_time_of_day(self) -> str:
        if 6 <= self.current_hour < 18:
            return "Day"
        if 18 <= self.current_hour < 22:
            return "Sunset"
        return "Night"

    def get_current_season(self) -> str:
        return SEASONS[(self.current_day // 7) % 4]

    def advance_time(self):
        prev_hour = self.current_hour
        self.current_hour = (self.current_hour + 1) % 24
        if self.current_hour == 0 and prev_hour == 23:
            self.current_day += 1
        if self.current_hour < 20:
            self.event = "Nothing"
        elif self.current_hour >= 20:
            if self.event == "Nothing":
                if random.randint(1, 100) <= 20:
                    self.event = "Full Moon"
                else:
                    self.event = "Nothing"
        self.roll_daily_event_if_needed()
        self.update_floating_island_state()

    # -------------- Quests --------------
    def show_quest_menu(self):
        while True:
            clear_screen()
            print(f"_____QUEST ZONE: {self.current_zone}_____")
            quests = self.quest_manager.get_quests_for_zone(self.current_zone)
            for idx, q in enumerate(quests, 1):
                if q.quest_type == 1:
                    desc = f"Catch {q.amount} {q.target_fish}"
                else:
                    desc = f"Catch {q.amount} {q.rarity} Fish"
                status = "Finished" if q.is_completed() else "Didn't Finish"
                print(f"{idx}. {desc} ({status})")
            print("0. Return to main menu")
            choice = input("Select a quest: ")
            if choice == '0':
                break
            if choice.isdigit() and 1 <= int(choice) <= len(quests):
                self.show_quest_detail(int(choice) - 1)

    def show_quest_detail(self, quest_index: int):
        while True:
            clear_screen()
            quests = self.quest_manager.get_quests_for_zone(self.current_zone)
            if quest_index < 0 or quest_index >= len(quests):
                return
            q = quests[quest_index]
            if q.quest_type == 1:
                requirement = f"Catch {q.amount} {q.target_fish}"
            else:
                requirement = f"Catch {q.amount} {q.rarity} Fish"
            print(f"___Quest{quest_index+1:02d}___")
            print(f"1. Requirement: {requirement}")
            print(f"2. Reward: Gain money: {q.reward}")
            print(f"3. Progress: {q.progress}/{q.amount}")
            print("4. Finish")
            print("0. Return")
            choice = input("Choose: ")
            if choice == '4':
                if q.is_completed():
                    reward = self.quest_manager.finish_quest(self.current_zone, quest_index)
                    self.balance += reward
                    self.save_game()
                    print(f"Quest completed! You gained {reward}$")
                    input("Press Enter to continue...")
                    break
                else:
                    print("You haven't met the requirements yet.")
                    input("Press Enter to continue...")
            elif choice == '0':
                break

    # -------------- Menu --------------
    def show_menu(self):
        clear_screen()
        xp_needed = self.calculate_xp_for_level(self.level)
        if self.level >= 100:
            xp_percent = 100
        else:
            xp_percent = round((self.xp / xp_needed) * 100, 2) if xp_needed else 0
        print("_____MENU_____")
        print(f"Level: {self.level} ({xp_percent}%)")
        print(f"Balance: {round(self.balance, 2)}$")
        time_of_day = self.get_time_of_day()
        season = self.get_current_season()
        emoji = SEASON_EMOJI.get(season, "")
        print(f"Time: {self.current_hour:02d}:00 ({time_of_day})")
        print(f"Day: {self.current_day} | Season: {season} {emoji}")
        print(f"Event: {self.event}")
        if self.daily_event is None:
            print("Today's Event: Normal Day")
        else:
            desc = DAILY_EVENT_EFFECTS.get(self.daily_event, "")
            print(f"Today's Event: {self.daily_event} – {desc}")
        if self.has_floating_key:
            if self.floating_island_visible:
                print("Floating Island: VISIBLE (12–16h)")
            else:
                print("Floating Island: Hidden (12–16h window)")
        print("Version: Beta")
        print(
            f"Fish Traps: {self.inventory_fish_traps} | "
            f"Bait N:{self.baits['normal']} A:{self.baits['advanced']} "
            f"E:{self.baits['expert']} L:{self.baits['legend']}"
        )
        print("1. Fishing")
        print("2. Fast Fishing (Catch multiple fish at once)")
        print("3. Zone")
        print("4. Sell fish")
        print("5. Inventory")
        print("6. Shop")
        print("7. Discovery Book")
        print("8. Quest")
        print("9. Exit game")
        print("10. Fish Trap Shop   (buy traps & bait)")
        print("11. Fish Trap        (manage traps)")

    # -------------- Fishing --------------
    def start_fishing(self):
        clear_screen()
        print(f"You cast your fishing rod in {self.current_zone} zone...")
        time.sleep(0.8)
        frames = [
            "        |",
            "        |",
            "        |",
            "        |",
            "       ---",
            r"      /   \ ",
            "     |     |",
            r"      \___/",
        ]
        for line in frames:
            print(line)
            time.sleep(0.3)
        print(f"Current streak: {self.streak}")
        is_exotic = False
        wait_seconds = 2
        while True:
            print(f"\nWaiting for a bite... (Streak: {self.streak})")
            time.sleep(wait_seconds)
            fish_bite = random.randint(1, 100) <= 60
            if fish_bite:
                print("\n>>> Fish Bite! <<<")
                time.sleep(1)
                if (self.current_zone == "Bathyal" and self.event == "Full Moon" \
                        and random.randint(1, 100) <= 100):
                    is_exotic = True
                    print(">>> Something Stranger Bite! <<<")
                    print(">>> Your minigame will x10 speed! <<<")
                    print(">>> Your catch zone will be 2 <<<")
                    success = self.start_minigame(full_moon_event=True)
                else:
                    success = self.start_minigame()
                if success:
                    self.obtain_fish(full_moon_event=is_exotic)
                else:
                    if self.streak > 0:
                        print("The fish run and you lost the streak")
                    self.streak = 0
                    input("Press Enter to continue...")
                break
            else:
                wait_seconds = min(wait_seconds + 1, 6)

    def fast_fishing(self):
        clear_screen()
        amount_str = input("How many fish do you want to catch? (1-10): ")
        if not amount_str.isdigit():
            print("Invalid amount.")
            input("Press Enter to return to menu")
            return
        amount = int(amount_str)
        if amount < 1 or amount > 10:
            print("Invalid amount.")
            input("Press Enter to return to menu")
            return
        cost = round((amount - 1) * self.fast_fishing_price, 2)
        if self.balance < cost:
            print("❌ Not enough money for fast fishing!")
            input("Press Enter to return to menu")
            return
        self.balance -= cost
        allowed_rarities = ["Common", "Uncommon", "Rare", "Epic", "Mythical", "Legendary"]
        base_list = list(self.current_fish_list)
        if self.daily_event in ("Exotic Surge", "Full Moon Night"):
            allowed_rarities.append("Exotic")
            base_list += EXOTIC_FISH_FULL_MOON
        valid_fish = [
            f for f in base_list
            if f.get('rarity') in allowed_rarities
        ]
        caught = []
        total_xp = 0
        for i in range(amount):
            if i > 0 and random.random() < 0.3:
                print("Autofish failed! The fish escaped.")
                continue
            time_of_day = self.get_time_of_day()
            season = self.get_current_season()
            filtered = []
            for fish in valid_fish:
                allowed_times = fish.get('time_of_day')
                allowed_seasons = fish.get('seasons')
                if allowed_times and time_of_day not in allowed_times:
                    continue
                if allowed_seasons and season not in allowed_seasons:
                    continue
                filtered.append(fish)
            if not filtered:
                filtered = valid_fish
            weights = {
                'Common': 5,
                'Uncommon': 3,
                'Rare': 2,
                'Epic': 1,
                'Legendary': 1,
                'Mythical': 1,
                'Exotic': 1 if self.daily_event in ("Exotic Surge", "Full Moon Night") else 0,
            }
            rare_types = {'Rare', 'Epic', 'Legendary', 'Mythical'}
            if self.daily_event in ("Exotic Surge", "Full Moon Night"):
                rare_types.add('Exotic')
            rare_weighted = []
            common_weighted = []
            for fish in filtered:
                rarity = fish.get('rarity', 'Common')
                weight = weights.get(rarity, 3)
                if rarity in rare_types:
                    rare_weighted.extend([fish] * weight)
                else:
                    common_weighted.extend([fish] * weight)
            if rare_weighted:
                total_weight = len(rare_weighted) + len(common_weighted)
                base_chance = len(rare_weighted) / total_weight * 100
                if self.daily_event == "Streak Madness":
                    bonus = min(self.streak * 5, 40)
                else:
                    bonus = min(self.streak * 2, 20)
                chance = base_chance + bonus
                chance = min(chance, 100)
                pool = rare_weighted if random.randint(1, 100) <= chance else common_weighted
            else:
                pool = common_weighted or filtered
            fish = random.choice(pool).copy()
            weight_val = self.generate_weight(fish['name'], fish['rarity'])
            fish['weight'] = round(weight_val, 1)
            if self.current_zone == "Sea":
                price_multiplier = SEA_PRICE_MULTIPLIER.get(fish['rarity'], 1)
                price = round(fish.get('base_price', fish.get('price', 0)) * price_multiplier, 2)
            elif self.current_zone == "Bathyal":
                price = fish.get('base_price', fish.get('price', 0))
            else:
                price = fish.get('price', 0)
            fish['price'] = price
            entry = {
                'name': fish['name'],
                'rarity': fish['rarity'],
                'price': fish['price'],
                'weight': fish['weight'],
                'zone': self.current_zone,
            }
            self.inventory.append(entry.copy())
            xp_gain = self.get_xp_by_rarity(fish['rarity'])
            if self.daily_event == "Double XP Day":
                xp_gain *= 2
            self.xp += xp_gain
            total_xp += xp_gain
            self.check_level_up()
            if self.daily_event == "Treasure Hunt" and random.random() < 0.10:
                bonus_money = random.randint(500, 2000)
                self.balance += bonus_money
                print(f"💰 Treasure Hunt! You found {bonus_money}$!")
            value = round(fish['weight'] * fish['price'], 2)
            self.update_discovery(self.current_zone, fish['name'], fish['weight'], value)
            self.quest_manager.update_quest_progress(self.current_zone, fish['name'], fish['rarity'])
            caught.append(entry)
        self.fast_fishing_price = round(self.fast_fishing_price * 1.005, 4)
        self.save_game()
        print("\nFast fishing results:")
        for f in caught:
            color = self.get_rarity_color(f['rarity'])
            print(color_text(f"- {f['name']} [{f['rarity']}] - {f['weight']} kg", color))
        print(f"Total XP gained: {total_xp}")
        print(f"Money spent: {cost}$")
        print(f"Current streak: {self.streak}")
        input("Press Enter to continue...")

    def start_minigame(self, full_moon_event=False) -> bool:
        bar = "--------------------------"  # length 26
        if full_moon_event:
            zone_length = 2
            speed = 0.01
        else:
            zone_length = self.current_zone_catch_length
            speed = self.get_speed()
        if self.daily_event == "Speedy Fisher":
            speed *= 1.3
        margin = 1
        zone_start = random.randint(5, len(bar) - zone_length)
        zone_end = zone_start + zone_length - 1
        extended_start = max(0, zone_start - margin)
        extended_end = min(len(bar) - 1, zone_end + margin)
        with RawInput():
            i = 0
            while i < len(bar):
                clear_screen()
                before = bar[:i]
                after = bar[i+1:]
                line = before + "|" + after
                target_line = ''.join('=' if zone_start <= j <= zone_end else ' ' for j in range(len(bar)))
                print("Catch zone:")
                print(line)
                print(target_line)
                start_time = time.time()
                key = None
                while time.time() - start_time < speed:
                    if key_pressed():
                        key = read_key()
                        break
                    time.sleep(0.001)
                # Handle key presses that occur exactly as the timer ends
                if key is None and key_pressed():
                    key = read_key()
                if key == ' ' or key in ENTER_KEYS:
                    pos = i
                    if extended_start <= pos <= extended_end:
                        print("\n>> Success! You caught a fish!")
                        return True
                    else:
                        print("\n>> Oh no! The fish run!")
                        return False
                i += 1
            print("\n>> Time's up! The fish escaped!")
        return False

    def obtain_fish(self, full_moon_event=False):
        if full_moon_event:
            fish = random.choice(EXOTIC_FISH_FULL_MOON).copy()
            fish['weight'] = random.randint(1000, 100000)
            price = fish['price']
        else:
            fish_list = list(self.current_fish_list)
            if self.daily_event in ("Exotic Surge", "Full Moon Night"):
                fish_list += EXOTIC_FISH_FULL_MOON
            fish = self.get_fish_by_weighted_random(fish_list)
            if fish is None:
                if self.streak > 0:
                    print("The fish run and you lost the streak")
                self.streak = 0
                return
            fish = fish.copy()
            weight = self.generate_weight(fish['name'], fish['rarity'])
            fish['weight'] = round(weight, 1)
            if self.current_zone == "Sea":
                price_multiplier = SEA_PRICE_MULTIPLIER.get(fish['rarity'], 1)
                price = round(fish.get('base_price', fish.get('price', 0)) * price_multiplier, 2)
            elif self.current_zone == "Bathyal":
                price = fish.get('base_price', fish.get('price', 0))
            else:
                price = fish.get('price', 0)
            fish['price'] = price
        weight = round(fish['weight'], 1)
        self.current_fish = {
            'name': fish['name'],
            'rarity': fish['rarity'],
            'price': fish['price'],
            'weight': weight,
            'zone': self.current_zone,
        }
        self.inventory.append(self.current_fish.copy())
        xp_gain = self.get_xp_by_rarity(fish['rarity'])
        if self.daily_event == "Double XP Day":
            xp_gain *= 2
        self.xp += xp_gain
        self.check_level_up()
        if self.daily_event == "Treasure Hunt" and random.random() < 0.10:
            bonus_money = random.randint(500, 2000)
            self.balance += bonus_money
            print(f"💰 Treasure Hunt! You found {bonus_money}$!")
        color = 'Red' if fish['rarity'] == 'Exotic' else self.get_rarity_color(fish['rarity'])
        print("\n" + color_text(f">> You caught a {fish['name']} [{fish['rarity']}] - {weight} kg.", color))
        value = round(weight * fish['price'], 2)
        self.update_discovery(self.current_zone, fish['name'], weight, value)
        self.quest_manager.update_quest_progress(self.current_zone, fish['name'], fish['rarity'])
        self.streak += 1
        print(f"Current streak: {self.streak}")
        if fish['name'] == 'Ancient Key' and not self.has_ancient_key:
            self.has_ancient_key = True
            print(">> You obtained the Ancient Key!")
        if self.current_zone == "Sea" and not self.has_floating_key and random.random() < 0.01:
            self.has_floating_key = True
            print("🔑 You found a mysterious FLOATING KEY hidden inside the fish!")
            print("☁️ Now you can access the Floating Island when it appears!")
            self.update_floating_island_state()
        self.save_game()
        input("Press Enter to continue...")

    # -------------- Inventory / Selling --------------
    def sell_fish(self):
        clear_screen()
        if not self.inventory:
            print("You have no fish to sell.")
            input("Press Enter to return to menu")
            return
        print("Fish in inventory:")
        for idx, f in enumerate(self.inventory, 1):
            color = self.get_rarity_color(f['rarity'])
            print(color_text(f"{idx}. {f['name']} [{f['rarity']}] - {f['weight']} kg", color))
        option = input("\nType 'all' to sell everything, or 'sell x Name' (e.g., sell x2 Carp): ")
        if option == 'all':
            total = sum(f['weight'] * f['price'] for f in self.inventory)
            jackpot = False
            if self.daily_event == "Jackpot Sell" and random.random() < 0.05:
                total *= 3
                jackpot = True
            total = round(total, 2)
            self.balance += total
            self.inventory = []
            if jackpot:
                print(f"\n💎 Jackpot! You earned {total}$ from selling all fish.")
            else:
                print(f"\nYou earned {total}$ from selling all fish.")
            self.save_game()
            input("Press Enter to return to menu")
            return
        elif option.startswith('sell x'):
            try:
                parts = option.split()
                amount = int(parts[1][1:])  # after 'x'
                name = ' '.join(parts[2:])
            except Exception:
                print("\nInvalid input.")
                input("Press Enter to return to menu")
                return
            found = [f for f in self.inventory if f['name'] == name]
            if len(found) < amount:
                print(f"\nYou don't have enough '{name}' to sell.")
            else:
                sell_list = found[:amount]
                sell_value = 0
                for fish in sell_list:
                    sell_value += fish['weight'] * fish['price']
                    self.inventory.remove(fish)
                jackpot = False
                if self.daily_event == "Jackpot Sell" and random.random() < 0.05:
                    sell_value *= 3
                    jackpot = True
                sell_value = round(sell_value, 2)
                self.balance += sell_value
                if jackpot:
                    print(f"\n💎 Jackpot! You sold {amount} {name} for {sell_value}$")
                else:
                    print(f"\nYou sold {amount} {name} for {sell_value}$")
                self.save_game()
            input("Press Enter to return to menu")
            return
        else:
            print("\nInvalid input.")
            input("Press Enter to return to menu")

    def show_inventory(self):
        clear_screen()
        if not self.inventory:
            print("Your fish inventory is empty.")
        else:
            print("Your Fish Inventory:")
            for idx, fish in enumerate(self.inventory, 1):
                color = self.get_rarity_color(fish['rarity'])
                print(color_text(f"{idx}. {fish['name']} [{fish['rarity']}] - {round(fish['weight'],1)} kg", color))
        input("Press Enter to return to menu")

    # -------------- Discovery Book --------------
    def show_discovery_book(self):
        clear_screen()
        print("Discovery Book:")
        print("1. Lake")
        print("2. Sea")
        print("3. Bathyal")
        print("4. Mystic Spring")
        print("5. Abyss Trench")
        print("6. Ancient Sea")
        print("7. Floating Island")
        choice = input("Pick a zone (1-7): ")
        mapping = {
            "1": ("Lake", FISH_LAKE),
            "2": ("Sea", FISH_SEA),
            "3": ("Bathyal", FISH_BATHYAL),
            "4": ("Mystic Spring", FISH_MYSTIC_SPRING),
            "5": ("Abyss Trench", FISH_ABYSS_TRENCH),
            "6": ("Ancient Sea", FISH_ANCIENT_SEA),
            "7": ("Floating Island", FISH_FLOATING_ISLAND),
        }
        if choice not in mapping:
            return
        zone, fish_list = mapping[choice]
        clear_screen()
        zone_data = self.discovery.get(zone, {})
        total = len(fish_list)
        found = sum(1 for f in fish_list if f['name'] in zone_data)
        percent = round((found / total) * 100, 0) if total else 0
        print(f"→ You have discovered {found}/{total} fish ({percent}%)")
        print()
        for f in fish_list:
            if f['name'] in zone_data:
                entry = zone_data[f['name']]
                color = self.get_rarity_color(f['rarity'])
                value = round(entry['maxValue'], 2)
                print(color_text(
                    f"{f['name']} [{f['rarity']}] - Times: {entry['count']} - Heaviest: {entry['maxWeight']} kg - Max Value: {value}$",
                    color))
            else:
                print("??? [--] - Times: -- - Heaviest: -- kg - Max Value: --")
        input("Press Enter to return to menu")

    # -------------- Shop --------------
    def show_shop(self):
        clear_screen()
        print("Shop - Buy Items:")
        for idx, item in enumerate(SHOP_ITEMS, 1):
            print(f"{idx}. {item['name']} - Price: {item['price']}$")
            print(f"    {item['description']}")
        choice = input("Enter item number to buy, or '0' to return: ")
        if choice == '0':
            return
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(SHOP_ITEMS):
            print("Invalid choice.")
            time.sleep(2)
            return
        selected = SHOP_ITEMS[int(choice) - 1]
        if self.balance < selected['price']:
            print("Not enough money to buy this item.")
            time.sleep(2)
            return
        if selected['name'] == 'Submarine Upgrade 02' and not self.has_ancient_key:
            print("You need the Ancient Key to buy this upgrade.")
            time.sleep(2)
            return
        if selected['name'] == 'Submarine Upgrade 02' and not self.has_abyss_trench_access:
            print("You need Submarine Upgrade 01 first.")
            time.sleep(2)
            return
        self.balance -= selected['price']
        name = selected['name']
        if name == 'Submarine':
            self.has_submarine = True
            print("Congratulations! You bought a Submarine and can now access Bathyal zone.")
        elif name == 'Boat':
            self.has_boat = True
            print("Congratulations! You bought a Boat and can now access Sea zone.")
        elif name == 'Torch':
            self.has_torch = True
            print("Congratulations! You bought a Torch and can now access Mystic Spring.")
        elif name == 'Submarine Upgrade 01':
            self.has_abyss_trench_access = True
            print("Congratulations! You bought Submarine Upgrade 01 and can now access Abyss Trench.")
        elif name == 'Submarine Upgrade 02':
            self.has_ancient_sea_access = True
            print("Congratulations! You bought Submarine Upgrade 02 and can now access Ancient Sea.")
        else:
            print(f"You bought {name}.")
        self.save_game()
        time.sleep(2)

    # [FISH_TRAP SHOP]
    def bait_trap_shop_menu(self):
        while True:
            clear_screen()
            print("Fish Trap Shop")
            print(f"Balance: {round(self.balance,2)}$")
            print(
                f"1. Fish Trap - {BAIT_PRICES['trap']}$ (Stock: {self.inventory_fish_traps})"
            )
            print(
                f"2. Normal Bait - {BAIT_PRICES['normal']}$ (Stock: {self.baits['normal']})"
            )
            print(
                f"3. Advanced Bait - {BAIT_PRICES['advanced']}$ (Stock: {self.baits['advanced']})"
            )
            print(
                f"4. Expert Bait - {BAIT_PRICES['expert']}$ (Stock: {self.baits['expert']})"
            )
            print(
                f"5. Legend Bait - {BAIT_PRICES['legend']}$ (Stock: {self.baits['legend']})"
            )
            print("0. Return")
            choice = input("Choose item: ")
            if choice == '0':
                return
            mapping = {'1': 'trap', '2': 'normal', '3': 'advanced', '4': 'expert', '5': 'legend'}
            if choice not in mapping:
                print("Invalid choice.")
                time.sleep(2)
                continue
            qty = input("Quantity to buy: ")
            if not qty.isdigit() or int(qty) <= 0:
                print("Invalid quantity.")
                time.sleep(2)
                continue
            qty = int(qty)
            item = mapping[choice]
            cost = BAIT_PRICES[item] * qty
            if self.balance < cost:
                print("Not enough balance.")
                time.sleep(2)
                continue
            self.balance -= cost
            if item == 'trap':
                self.inventory_fish_traps += qty
            else:
                self.baits[item] += qty
            print("Purchase successful!")
            self.save_game()
            time.sleep(2)

    # [FISH_TRAP HELPERS]
    def get_active_traps(self):
        return self.active_traps

    def add_active_trap(self, trap: Dict):
        self.active_traps.append(trap)

    def remove_active_trap(self, idx: int):
        if 0 <= idx < len(self.active_traps):
            self.active_traps.pop(idx)

    # [FISH_TRAP MENU]
    def fish_trap_menu(self):
        while True:
            clear_screen()
            print("Fish Trap")
            print("1. Set Fish Trap")
            print("2. Check Fish Trap")
            print("0. Return to menu")
            choice = input("Choose: ")
            if choice == '1':
                self.set_fish_trap_menu()
            elif choice == '2':
                self.check_fish_trap_menu()
            elif choice == '0':
                return
            else:
                print("Invalid choice.")
                time.sleep(1)

    def set_fish_trap_menu(self):
        if self.inventory_fish_traps < 1 or all(v == 0 for v in self.baits.values()):
            print("You need a Fish Trap and bait to set a trap.")
            time.sleep(2)
            return
        if len(self.active_traps) >= TRAP_MAX_ACTIVE:
            print("You have reached the active trap limit (10).")
            time.sleep(2)
            return
        zones = self.get_unlocked_zones()
        while True:
            clear_screen()
            print("Choose zone:")
            for idx, z in enumerate(zones, 1):
                print(f"{idx}. {z}")
            print("0. Cancel")
            choice = input("Zone: ")
            if choice == '0':
                return
            if choice.isdigit() and 1 <= int(choice) <= len(zones):
                zone = zones[int(choice) - 1]
                break
            else:
                print("Invalid choice.")
                time.sleep(1)
        available = [b for b, c in self.baits.items() if c > 0]
        bait_names = {
            'normal': 'Normal Bait',
            'advanced': 'Advanced Bait',
            'expert': 'Expert Bait',
            'legend': 'Legend Bait',
        }
        while True:
            clear_screen()
            print("Choose bait:")
            for idx, b in enumerate(available, 1):
                print(f"{idx}. {bait_names[b]} (Stock: {self.baits[b]})")
            print("0. Cancel")
            choice = input("Bait: ")
            if choice == '0':
                return
            if choice.isdigit() and 1 <= int(choice) <= len(available):
                bait = available[int(choice) - 1]
                break
            else:
                print("Invalid choice.")
                time.sleep(1)
        self.inventory_fish_traps -= 1
        self.baits[bait] -= 1
        trap = {
            'zone': zone,
            'bait': bait,
            'real_start_ts': time.time(),
            'duration_seconds': REAL_SECONDS_PER_INGAME_DAY,
            'overdue_seconds': TRAP_OVERDUE_SECONDS,
            'capacity_max': TRAP_CAPACITY_MAX,
            'caught_count': 0,
        }
        self.add_active_trap(trap)
        self.save_game()
        print(f"Fish Trap set in {zone} using {bait_names[bait]}.")
        time.sleep(2)

    def check_fish_trap_menu(self):
        if not self.active_traps:
            print("No active traps.")
            time.sleep(2)
            return
        bait_names = {
            'normal': 'Normal Bait',
            'advanced': 'Advanced Bait',
            'expert': 'Expert Bait',
            'legend': 'Legend Bait',
        }
        while True:
            clear_screen()
            print("Active Fish Traps:")
            for idx, trap in enumerate(self.active_traps, 1):
                elapsed = time.time() - trap['real_start_ts']
                duration = trap['duration_seconds']
                overdue = trap.get('overdue_seconds', TRAP_OVERDUE_SECONDS)
                if elapsed >= duration:
                    status = 'READY'
                    if elapsed >= duration + overdue:
                        status = 'OVERDUE'
                else:
                    status = format_remaining_time(duration - elapsed)
                print(f"{idx}. Fish Trap {idx:02d} - {trap['zone']} ({status})")
            print("0. Return")
            choice = input("Select trap: ")
            if choice == '0':
                return
            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(self.active_traps):
                continue
            idx = int(choice) - 1
            trap = self.active_traps[idx]
            elapsed = time.time() - trap['real_start_ts']
            duration = trap['duration_seconds']
            overdue = trap.get('overdue_seconds', TRAP_OVERDUE_SECONDS)
            if elapsed >= duration + overdue:
                print("The trap was overdue and broke.")
                self.remove_active_trap(idx)
                self.save_game()
                time.sleep(2)
                continue
            if elapsed >= duration:
                results, _ = self.resolve_trap(trap)
                self.remove_active_trap(idx)
                self.save_game()
                print(f"You collected {len(results)} fish!")
                time.sleep(2)
                continue
            remaining = duration - elapsed
            clear_screen()
            print(f"Fish caught: {trap['caught_count']}/{trap['capacity_max']}")
            print(f"Remaining time: {format_remaining_time(remaining)}")
            print("Bait: " + bait_names.get(trap['bait'], ''))
            input("Press Enter to return...")

    def resolve_trap(self, trap: Dict):
        zone = trap['zone']
        bait = trap['bait']
        fish_list = self.get_fish_list_for_zone(zone)
        results = []
        total_xp = 0
        count = random.randint(3, 7)
        for _ in range(count):
            if bait == 'legend':
                if random.random() < 0.4:
                    boss_entry = next((f for f in fish_list if f['rarity'] == '???'), None)
                    if boss_entry:
                        weight = random.randint(1000, 10000)
                        price = boss_entry.get('price', boss_entry.get('base_price', 0))
                        entry = {
                            'name': boss_entry['name'],
                            'rarity': '???',
                            'price': price,
                            'weight': weight,
                            'zone': zone,
                        }
                        self.inventory.append(entry.copy())
                        value = round(weight * price, 2)
                        self.update_discovery(zone, entry['name'], weight, value)
                        xp_gain = boss_entry.get('xp', 0)
                        if self.daily_event == 'Double XP Day':
                            xp_gain *= 2
                        self.xp += xp_gain
                        total_xp += xp_gain
                        self.quest_manager.update_quest_progress(zone, entry['name'], '???')
                        results.append(entry)
                        continue
                filtered = [f for f in fish_list if f['rarity'] == 'Exotic']
                if not filtered:
                    filtered = [f for f in fish_list if f['rarity'] != '???']
                fish = random.choice(filtered).copy()
            else:
                filtered = [
                    f for f in fish_list
                    if f['rarity'] in BAIT_RARITY_MAP.get(bait, []) and f['rarity'] != '???'
                ]
                if not filtered:
                    filtered = [f for f in fish_list if f['rarity'] != '???']
                fish = random.choice(filtered).copy()
            weight_val = self.generate_weight(fish['name'], fish['rarity'])
            fish['weight'] = round(weight_val, 1)
            if zone == 'Sea':
                price_multiplier = SEA_PRICE_MULTIPLIER.get(fish['rarity'], 1)
                price = round(fish.get('base_price', fish.get('price', 0)) * price_multiplier, 2)
            elif zone == 'Bathyal':
                price = fish.get('base_price', fish.get('price', 0))
            else:
                price = fish.get('price', 0)
            fish['price'] = price
            entry = {
                'name': fish['name'],
                'rarity': fish['rarity'],
                'price': price,
                'weight': fish['weight'],
                'zone': zone,
            }
            self.inventory.append(entry.copy())
            value = round(fish['weight'] * price, 2)
            self.update_discovery(zone, fish['name'], fish['weight'], value)
            xp_gain = self.get_xp_by_rarity(fish['rarity'])
            if self.daily_event == 'Double XP Day':
                xp_gain *= 2
            self.xp += xp_gain
            total_xp += xp_gain
            self.quest_manager.update_quest_progress(zone, fish['name'], fish['rarity'])
            results.append(entry)
        self.check_level_up()
        return results, total_xp

    # -------------- Main loop --------------
    def run(self):
        while True:
            self.show_menu()
            choice = input("Pick your choice (1-11): ")
            if choice == '1':
                self.start_fishing()
                self.advance_time()
            elif choice == '2':
                self.fast_fishing()
                self.advance_time()
            elif choice == '3':
                self.choose_zone()
            elif choice == '4':
                self.sell_fish()
            elif choice == '5':
                self.show_inventory()
            elif choice == '6':
                self.show_shop()
            elif choice == '7':
                self.show_discovery_book()
            elif choice == '8':
                self.show_quest_menu()
            elif choice == '9':
                break
            elif choice == '10':
                self.bait_trap_shop_menu()
            elif choice == '11':
                self.fish_trap_menu()
            elif choice == 'admin':
                self.balance += 1000000000
                print("🛠️ Admin mode activated! You received 1,000,000,000$")
                self.save_game()
                time.sleep(2)
            else:
                print("Invalid choice.")
                time.sleep(1)

# --------------------------- Main entry ---------------------------

def main():
    game = Game()
    game.run()

if __name__ == '__main__':
    main()
