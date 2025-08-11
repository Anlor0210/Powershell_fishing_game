🎣 Fishing Game Tutorial – Full Guide
👋 1. Welcome
Welcome to Fishing Game, a simple yet addictive console-based fishing simulator powered by Python!
If you don't have Python, download it here: https://www.python.org/downloads
No fancy graphics. Just you, the water, and a whole lot of fish!
📦 2. Installation & Setup
🔽 Step 1: Download and unzip the game
Unzip the .zip file to any folder on your computer.
🚀 Step 2: Start the game
Double-click on the fishing.py file.
The game will open in a PowerShell window (or CMD if preferred).
✅ Requires Python installed (e.g., Python 3.11+)
🎮 3. How to Fish
🎣 Step-by-step:
From the Main Menu, select 1. Start Fishing (Normal Fishing) or 2. Fast Fishing.
Wait until the pointer is inside the Catch Zone.
Press Space to catch the fish! (Previously Enter; changed for better gameplay feel.)
📌 Catch Zone
diff
Copy
Edit
Catch zone:
-----------|--------------
===
→ Try to hit Space when the pointer (|) is inside the === zone.
🆕 New Gameplay Systems
Streak System
Catching fish in Normal Fishing increases your streak count.
Higher streaks = higher rare fish and Boss spawn chance.
Missing a catch resets streak with the message:
"The fish run and you lost the streak".
Fast Fishing does not affect streak, but XP is still earned normally.
📊 Streak Spawn Rate Formula:
Streak	Rare Fish Chance Boost	Boss Spawn Chance Boost
0	+0%	+0%
1–4	+5% each streak	+0.2% each streak
5–9	+6% each streak	+0.25% each streak
10+	+7% each streak	+0.3% each streak
(These percentages are added on top of the base spawn rate of the zone)
Boss Minigame
Boss fish have a rare base spawn chance (1%), increased by streak bonus.
Special fight with Stage 1 & Stage 3 mini-games only.
Fast Fishing Updates
Now has a 30% chance to miss automatically.
Price per extra fish starts at 15$ and increases by 0.5% after each Fast Fishing.
No streak bonus, but XP is still given for all catches.
🌍 4. Fishing Zones
Unlock and travel to many fishing zones, such as:
Lake, Mystic Spring, Deep Sea, Frozen Bay, Abyss Trench...
Each zone has its own fish species and quest sets.
📘 5. Quest System (Menu 7)
Each zone has 10 unique quests, auto-generated.
Two quest types:
Catch specific fish (e.g., "Catch 5 Snakefish")
Catch by rarity (e.g., "Catch 3 Uncommon fish")
Quest Example:
markdown
Copy
Edit
___ Quests (Zone: Lake) ___
1.	Catch 5 Snakefish         Status: In Progress (2/5)
2.	Catch 3 Uncommon Fish     Status: Completed (3/3)
Completing quests gives coins and XP, and a new quest replaces the old one instantly.
🎒 6. Inventory (Menu 4)
View caught fish, rarity, and weight.
Sell individual fish or all at once.
🛒 7. Shop (Menu 5)
Spend coins to:
Unlock new zones.
Buy better gear and upgrades.
📔 8. Discovery Log (Menu 6)
Track every fish species you’ve caught.
Each zone keeps a separate record.
💾 9. Auto-Save
The game auto-saves after:
Catching fish
Completing quests
Buying items
🙏 10. Thank You!
Thanks for playing the Fishing Game!
Stay relaxed, chase rare fish, and enjoy our evolving quest & streak system.
If you enjoy the game, share it with friends!
Contact: An1002@gmail.com
The game is updated weekly!
