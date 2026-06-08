import telebot
import sqlite3
import re
import time
import random
import firebase_admin
from firebase_admin import credentials, db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import threading
import requests  # 👈 አውቶማቲክ ዲፖዚት ለመፈተሽ የተጨመረ


                 
# 1. መጀመሪያ ፋንክሽኑ ይፈጠር (ከላይ)
# 3. Listener-ውን አንድ ጊዜ ብቻ ማስጀመር
def cards_listener(event):
    if event.data:
        # ለቴሌግራም ቦትህ ማሳወቂያ መላክ
        # ቦቶቹ live_players ውስጥ ስለገቡ፣ ለተጫዋቾች እንዲታዩ አድርግ
        players_count = len(event.data) if isinstance(event.data, dict) else 0
        print(f"✅ አዲስ ለውጥ ተገኝቷል! ጠቅላላ ተጫዋቾች: {players_count}")
        
        
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://my-app-project-1e0bb-default-rtdb.firebaseio.com/'
        })
    # የ Listener-ው መጀመሪያ እዚህ ብቻ ነው መሆን ያለበት

    db.reference('live_players').listen(cards_listener)
    print("🎧 ሊስነር ተጀምሯል!")
except Exception as e:
    print(f"❌ ስህተት: {e}")
              

# --- 2. የቦት መረጃዎች ---
API_TOKEN = '8407193497:AAGAxmT-zgvNd24CUoQoEOYcTxVyHZuQkLE'
bot = telebot.TeleBot(API_TOKEN)
# --- ይህንን ኮድ አስገባ ---

# ቀደም ብለው ቦነስ የወሰዱ ተጠቃሚዎች መታወቂያ መያዣ
users_with_bonus = set()
# main.py ላይ ያለውን የቦት መቆጣጠሪያ ክፍል እንደዚህ ቀይረው

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    # እዚህ የምትፈልጋቸውን አዝራሮች ለየብቻ በዝርዝር አስቀምጣቸው
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Register"), KeyboardButton("Play"))
    markup.add(KeyboardButton("Balance"), KeyboardButton("Deposit"))
    markup.add(KeyboardButton("Invite"))
    
    bot.send_message(user_id, "እንኳን ወደ Jobe Bingo በደህና መጡ! ከታች ያለውን ሜኑ ይምረጡ።", reply_markup=markup)
ADMIN_ID = 384408623 
WEB_APP_URL = "https://amanzewdu4117-dev.github.io/bingobot/" 
FIREBASE_URL = "https://my-app-project-1e0bb-default-rtdb.firebaseio.com" # 👈 የተጨመረ

active_players_in_game = {}

# 📌 Mock functions for missing balance updates in original snippet
def update_balance(user_id, amount):
    try:
        conn = sqlite3.connect('bingo_data.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        # Also sync to firebase
        ref = db.reference(f'users/{user_id}')
        current = ref.child('balance').get() or 0
        ref.child('balance').set(current + amount)
    except Exception as e:
        print(f"Error updating balance: {e}")

def get_user_data(user_id):
    try:
        conn = sqlite3.connect('bingo_data.db')
        c = conn.cursor()
        c.execute("SELECT username, balance FROM users WHERE user_id = ?", (user_id,))
        res = c.fetchone()
        conn.close()
        if res: return res[0], res[1]
    except:
        pass
    ref = db.reference(f'users/{user_id}').get() or {}
    return ref.get('username', 'ተጫዋች'), ref.get('balance', 0.0)

def save_phone(user_id, phone):
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get()
    
    # ተጠቃሚው ቀድሞ ተመዝግቦ ከሆነ በድጋሚ ቦነስ አይስጠው
    if user_data and 'registered' in user_data:
        bot.send_message(user_id, "⚠️ ቀድሞውኑ ተመዝግበዋል! በድጋሚ ቦነስ አይሰጥም።")
        return

    # የመጀመሪያ ምዝገባ ከሆነ
    conn = sqlite3.connect('bingo_data.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, balance, is_bot) VALUES (?, 20.0, 0)", (user_id,))
    conn.commit()
    conn.close()
    
    # በ Firebase ላይ ተጠቃሚው መመዝገቡን ምልክት ማድረግ (registered: True)
    user_ref.update({
        'phone': phone,
        'balance': 20.0,
        'registered': True  # 👈 ይህ ምልክት እንደገና እንዳይመዘገብ ይረዳል
    })
    
    bot.send_message(user_id, "🎉 እንኳን ደስ አለዎት! ለምዝገባዎ 20 ETB ቦነስ ተቀብለዋል።")

def get_main_menu(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🕹️ Play Bingo", web_app=WebAppInfo(url=WEB_APP_URL)))
    markup.add(InlineKeyboardButton("💳 Balance", callback_data="bal"), InlineKeyboardButton("💰 Deposit", callback_data="dep"))
  
    return markup


# የኢትዮጵያዊ ስሞች ዝርዝር
ethiopian_names = [
    "አማኑኤል", "ቤተልሄም", "ዳዊት", "ጽዮን", "ዮሐንስ", "ሰላም", "ኪሩቤል", "ህይወት", 
    "ቴዎድሮስ", "እሌኒ", "አቤል", "ትግስት", "ሳሙኤል", "ማርያም", "ዘለቀ", "መቅደስ",
    "ገብሬ", "አበባ", "ሙሉቀን", "እመቤት", "ፍሬህይወት", "ዮናታን", "ሜላት", "ናትናኤል"
]

def auto_bot_injector():
    while True:
        game_ref = db.reference('liveGame')
        game_data = game_ref.get()

        if game_data and game_data.get('status') == 'waiting':
            current_cards = game_data.get('selectedCards', {})
            
            # ቦቶች ከ 40 መብለጥ የለባቸውም
            if len(current_cards) < 40:
                bot_id = f"c{random.randint(1, 500)}"
                
                # የተባዛ ካርድ እንዳይኖር መፈተሽ
                if bot_id not in current_cards:
                    # ሀገር በቀል ስም መምረጥ
                    chosen_name = random.choice(ethiopian_names)
                    
                    bot_data = {
                        'playerName': chosen_name,
                        'is_ai': True
                    }
                    db.reference(f'liveGame/selectedCards/{bot_id}').set(bot_data)
                    print(f"🤖 ቦት {chosen_name} በካርድ {bot_id} ገብቷል!")
        
        time.sleep(2) # በየ 2 ሰከንዱ ቦት ይጨምራል

# Thread ማስጀመሪያ
threading.Thread(target=auto_bot_injector, daemon=True).start()

def create_massive_bots(count=40):
    for i in range(1, count + 1):
        bot_id = f"bot_{i}"
        # 1 እስከ 500 ባለው ክልል ውስጥ ካርድ እንዲመርጡ እናደርጋለን
        random_card_id = random.randint(1, 500) 
        
        bot_data = {
            'playerName': f"AI_Player_{i}",
            'cardId': random_card_id, 
            'is_ai': True,
            'numbers': [random.randint(1, 75) for _ in range(15)]
        }
        
        # ቦቶቹን ወደ Firebase እንልካለን
        db.reference('live_players/' + bot_id).set(bot_data)

# ይህንን ተግባር አድሚን ዳሽቦርድ ላይ "ክተት" የሚለውን ቁልፍ ስትጫን እንዲሰራ አድርገው
def sync_bots_to_firebase():
    try:
        conn = sqlite3.connect('bingo_data.db')
        c = conn.cursor()
        c.execute("SELECT user_id, balance FROM users WHERE is_bot = 1")
        rows = c.fetchall()
        conn.close()
        
        ai_data = {}
        for row in rows:
            bot_id = f"bot_{row[0]}"
            ai_data[bot_id] = {
                "userId": bot_id,
                "username": f"Bot_{row[0]}",
                "balance": row[1],
                "is_ai": True
            }
        
        # 🛑 እዚህ ነው ችግሩ ሊሆን የሚችለው!
        # ተጫዋቾች የሚገቡበት ትክክለኛ Path ምንድነው? 
        # ለምሳሌ 'liveGame/selectedCards' ከሆነ እዚህ ጋር መቀየር አለበት።
        db.reference('liveGame/selectedCards').update(ai_data)
        
        print(f"✅ {len(rows)} ቦቶች ወደ Firebase ተልከዋል!")
        
    except Exception as e:
        print(f"❌ Error syncing bots: {e}")

# 📌 የተጫዋቾች መከታተያ Listener (በጣም አስተማማኝው ስሪት)

def process_winner_payout(winner_card_id):
    try:
        ref_selected = db.reference('liveGame/selectedCards')
        selected_cards = ref_selected.get()
        
        if not selected_cards:
            return 0

        if isinstance(selected_cards, list):
            selected_cards = {str(i): v for i, v in enumerate(selected_cards) if v is not None}

        # 💰 የገንዘብ እና የደራሽ ስሌት
        card_price = 10
        total_cards = len(selected_cards)
        total_pool = total_cards * card_price
        system_cut = total_pool * 0.15
        winner_prize = round(total_pool - system_cut, 2)

        card_key = f"c{winner_card_id}"
        if card_key not in selected_cards:
            card_key = str(winner_card_id)

        if card_key in selected_cards:
            is_bot = selected_cards[card_key].get('is_ai') == True
            
            # 👤 የአሸናፊውን ማንነት እና ስም መለየት
            if is_bot:
                winner_user_id = "bot_game_data"
                winner_info = "የሰፈር ቦት 🤖"
                print(f"🤖 አሸናፊው ቦት ስለሆነ የባንክ ክፍያ አልተፈጸመም።")
            else:
                winner_user_id = selected_cards[card_key].get('userId')
                if winner_user_id:
                    user_ref = db.reference(f'users/{winner_user_id}/balance')
                    current_bal = user_ref.get() or 0
                    new_bal = current_bal + winner_prize
                    user_ref.set(new_bal)
                    update_balance(winner_user_id, winner_prize)
                    print(f"💰 Payout: {winner_prize} ETB added to User {winner_user_id}")

            winner_info = db.reference(f'users/{winner_user_id}/name').get() or "ተጫዋች"
            
            # 🚀 ለዌብ ገጹ (Web App) መረጃ መላኪያ
            winner_data_for_web = {
            "winnerName": winner_info,
            "prize": winner_prize,
            "cardId": winner_card_id,
            "isAi": is_bot,
            "status": "winner_declared"
        }
        
        # 🔔 Firebase status ን ወደ 'finished' ቀይር (ይህ ነው ዌብሳይቱን የሚያሳየው)
        db.reference('liveGame').update({
            'winner_data': winner_data_for_web,
            'status': 'finished',
            'gameStatus': {'status': 'finished'}
        })
        
        # 📢 1. ለጌሙ ግሩፕ ማሳወቂያ ይልካል
        win_msg = (
            f"🏁 ━━━━━━━━━━━━━━━━━ 🏁\n"
            f"🎉 Congratulations! ቢንጎ! 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏆 የዚህ ዙር አሸናፊ፦ {winner_info} 🥳\n"
            f"💰 የበላው የደራሽ መጠን፦ {winner_prize} ETB 💸\n\n"
            f"⏳ ቀጣዩ ዙር በ 5 ሰከንድ ውስጥ ይጀምራል..."
        )
        
        GROUP_CHAT_ID = "-1003968758379"
        
        try:
            sent_message = bot.send_message(GROUP_CHAT_ID, win_msg, parse_mode="Markdown")
            
            # ⏳ 2. የ 5 ሰከንድ የቀጥታ Countdown
            for i in range(4, -1, -1):
                time.sleep(1)
                # ... (የ countdown_text አወቃቀርዎ እንደነበረ ይቆይ) ...
                try:
                    bot.edit_message_text(chat_id=GROUP_CHAT_ID, message_id=sent_message.message_id, text=countdown_text, parse_mode="Markdown")
                except Exception:
                    pass
        except Exception as msg_err:
            print(f"❌ Telegram Send Error: {msg_err}")

        # 3. ጨዋታው ሲያልቅ ወደ 'waiting' መልስ (ዌብሳይቱን ወደ አዲሱ ዙር እንዲሄድ ያደርገዋል)
        db.reference('liveGame').update({
            'status': 'waiting',
            'gameStatus': {'status': 'waiting'}
        })

        # 4. ለአሸናፊው በውስጥ መስመር
        if not is_bot and winner_user_id:
            try:
                bot.send_message(winner_user_id, win_msg, parse_mode="Markdown")
            except Exception:
                pass

        return winner_prize

    except Exception as e:
        print(f"❌ Payout Error: {e}")
        return


# --- 🎯 CENTRAL GAME ENGINE (AI የተወገደበት እና እውነተኛ ቢንጎ ፍተሻ) ---

def check_winner(card_numbers, drawn_numbers):
    """
    አንድ ተጫዋች 5x5 የቢንጎ ካርቴላ ላይ ቢያንስ አንድ መስመር (አግድም፣ ቁልቁል፣ ወይም ዲያጎናል) 
    መሙላቱን የሚፈትሽ ፋንክሽን።
    """
    if not card_numbers:
        return False
        
    drawn_set = set(drawn_numbers)
    drawn_set.add(0)  # የFREE ቦታን ሁልጊዜ እንደተመረጠ ይቁጠረው
    
    # 1. ካርታውን ወደ 5x5 Grid መቀየር
    grid = []
    
    # ካርታው 1D list (24 ወይም 25 ቁጥሮች) ከሆነ ወደ 2D መቀየር
    if not isinstance(card_numbers[0], list):
        if len(card_numbers) == 24:
            # መሃል ላይ 0 በመጨመር 25 ማድረግ
            temp_list = card_numbers[:12] + [0] + card_numbers[12:]
            grid = [temp_list[i:i+5] for i in range(0, 25, 5)]
        elif len(card_numbers) == 25:
            grid = [card_numbers[i:i+5] for i in range(0, 25, 5)]
        else:
            return False # ትክክለኛ የቢንጎ ካርታ አይደለም
    else:
        grid = card_numbers # አስቀድሞ 5x5 list ነው

    # 2. አግድም መስመሮችን መፈተሽ (Rows)
    for row in grid:
        if all(num in drawn_set for num in row):
            return True

    # 3. ቁልቁል መስመሮችን መፈተሽ (Columns)
    for col in range(5):
        if all(grid[row][col] in drawn_set for row in range(5)):
            return True

    # 4. ዲያጎናል መስመር 1 ( \ )
    if all(grid[i][i] in drawn_set for i in range(5)):
        return True

    # 5. ዲያጎናል መስመር 2 ( / )
    if all(grid[i][4 - i] in drawn_set for i in range(5)):
        return True

   #
def reset_game():
    """የጨዋታውን Firebase መረጃ ወደ መጀመሪያው ሁኔታ የሚመልስ ፋንክሽን"""
    print("🔄 ጨዋታው እየተጀመረ ነው... አሮጌ መረጃዎች እየተጸዱ ነው!")
    db.reference('liveGame/selectedCards').delete()
    db.reference('liveGame/history').delete()
    db.reference('liveGame/currentNumber').delete()
    db.reference('liveGame/winner').delete()
    
    # የጨዋታውን status ወደ waiting መቀየር
    db.reference('liveGame').update({
        'status': 'waiting',
        'timerStartTime': int(time.time() * 1000)
    })

def start_bingo_numbers():
    while True:
        try:
            print("🔄 NEW ROUND STARTING")
            db.reference('liveGame/selectedCards').set({})

            # 🔄 RESET GAME
            ref = db.reference('liveGame')
            ref.set({
                'status': 'waiting',
                'currentNumber': None,
                'history': [],
                'selectedCards': {},
                'winnerName': None,
                'timerStartTime': int(time.time() * 1000)
            })

            print("⏳ WAITING PLAYERS FOR 40 SECONDS...")
            time.sleep(40)

            selected_cards = db.reference('liveGame/selectedCards').get() or {}
            if not selected_cards:
                print("🛑 No Players Joined.")
                time.sleep(5)
                continue

            ref.update({'status': 'started'})
            print(f"🚀 GAME STARTED | Players: {len(selected_cards)}")
            
            shuffled_numbers = list(range(1, 76))
            random.shuffle(shuffled_numbers)
            
            called_numbers = []
            winner_found = False
            winner_info = "የሰፈር ቦት 🤖" # ነባሪ አሸናፊ

            # 🎯 CALL NUMBERS LOOP (እስከ 25ኛው ጥሪ)
            for i, number in enumerate(shuffled_numbers[:25], start=1):
                called_numbers.append(number)
                db.reference('liveGame').update({'currentNumber': number, 'history': called_numbers})
                print(f"🎯 Number #{i}: {number}")
                
                # 🤖 25ኛው ጥሪ ላይ ቦቱን በግድ አሸናፊ አድርግ
                if i == 25:
                    winner_found = True
                    break 

                time.sleep(1) # ቁጥር የመጥሪያ ፍጥነት

            # 🚀 አሸናፊው ከተገኘ በኋላ የሚፈጸም
            if winner_found:
                db.reference('liveGame').update({
                    'winnerName': winner_info,
                    'status': 'finished'
                })
                
                # 📢 ለቴሌግራም ማሳወቂያ
                GROUP_CHAT_ID = "-1003968758379"
                bot.send_message(GROUP_CHAT_ID, f"🏆 አሸናፊው፦ {winner_info} 🥳")
                print(f"✅ ጨዋታው ተጠናቋል! አሸናፊው፦ {winner_info}")
            
            time.sleep(10) # ለአሸናፊው ማሳያ ጊዜ

        except Exception as e:
            print(f"Error in game engine loop: {e}")
            time.sleep(5)def start_bingo_numbers():
    while True:
        try:
            print("🔄 NEW ROUND STARTING")
            db.reference('liveGame/selectedCards').set({})

            # 🔄 RESET GAME
            ref = db.reference('liveGame')
            ref.set({
                'status': 'waiting',
                'currentNumber': None,
                'history': [],
                'selectedCards': {},
                'winnerName': None,
                'timerStartTime': int(time.time() * 1000)
            })

            print("⏳ WAITING PLAYERS FOR 40 SECONDS...")
            time.sleep(40)

            selected_cards = db.reference('liveGame/selectedCards').get() or {}
            if not selected_cards:
                print("🛑 No Players Joined.")
                time.sleep(5)
                continue

            ref.update({'status': 'started'})
            print(f"🚀 GAME STARTED | Players: {len(selected_cards)}")
            
            shuffled_numbers = list(range(1, 76))
            random.shuffle(shuffled_numbers)
            
            called_numbers = []
            winner_found = False
            winner_info = "የሰፈር ቦት 🤖" # ነባሪ አሸናፊ

            # 🎯 CALL NUMBERS LOOP (እስከ 25ኛው ጥሪ)
            for i, number in enumerate(shuffled_numbers[:25], start=1):
                called_numbers.append(number)
                db.reference('liveGame').update({'currentNumber': number, 'history': called_numbers})
                print(f"🎯 Number #{i}: {number}")
                
                # 🤖 25ኛው ጥሪ ላይ ቦቱን በግድ አሸናፊ አድርግ
                if i == 25:
                    winner_found = True
                    break 

                time.sleep(1) # ቁጥር የመጥሪያ ፍጥነት

            # 🚀 አሸናፊው ከተገኘ በኋላ የሚፈጸም
            if winner_found:
                db.reference('liveGame').update({
                    'winnerName': winner_info,
                    'status': 'finished'
                })
                
                # 📢 ለቴሌግራም ማሳወቂያ
                GROUP_CHAT_ID = "-1003968758379"
                bot.send_message(GROUP_CHAT_ID, f"🏆 አሸናፊው፦ {winner_info} 🥳")
                print(f"✅ ጨዋታው ተጠናቋል! አሸናፊው፦ {winner_info}")
            
            time.sleep(10) # ለአሸናፊው ማሳያ ጊዜ

        except Exception as e:
            print(f"Error in game engine loop: {e}")
            time.sleep(5)                                        
                
@bot.callback_query_handler(func=lambda call: call.data == "with_start")
def withdraw_start(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    _, balance = get_user_data(user_id)
    if balance < 15:
        bot.send_message(user_id, f"❌ ማውጣት አይቻልም፦ አነስተኛው የማውጫ መጠን 15 ETB ነው። በአሁኑ ሰዓት ያለዎት ባላንስ፦ {balance} ETB ነው።")
        return
        
    msg = (
        "💸 የባላንስ ማውጫ ፎርም\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "እባክዎ ማውጣት የሚፈልጉትን የብር መጠን በቁጥር ብቻ ያስገቡ፦\n\n"
        f"📌 *የእርስዎ ባላንስ፦ {balance} ETB*"
    )
    sent_msg = bot.send_message(user_id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, get_withdraw_amount)

def get_withdraw_amount(message):
    user_id = message.chat.id
    text = message.text.strip()
    
    if not text.isdigit():
        sent_msg = bot.send_message(user_id, "❌ ስህተት ቁጥር ብቻ ያስገቡ (ምሳሌ: 100) 👇፦")
        bot.register_next_step_handler(sent_msg, get_withdraw_amount)
        return
        
    amount = float(text)
    _, balance = get_user_data(user_id)
    
    if amount > balance:
        bot.send_message(user_id, f"❌ ስህተት፦ በቂ ባላንስ የለዎትም። ከፍተኛ ማውጣት የሚችሉት መጠን፦ {balance} ETB")
        return
        
    if amount < 15:
        bot.send_message(user_id, "❌ አነስተኛው የማውጫ መጠን 15 ETB ነው።")
        return

    # ይህንን መስመር በፋንክሽኑ ውስጥ ባለው ስህተት ቦታ ይተኩት፡
        user_withdraw_data[user_id]={"amount": amount}
    
    msg = "🏦 የባንክ ስም ያስገቡ\n(ለምሳሌ፦ Telebirr, CBE, Commercial Bank...)"
    sent_msg = bot.send_message(user_id, msg)
    bot.register_next_step_handler(sent_msg, get_withdraw_bank)

def get_withdraw_bank(message):
    global user_withdraw_data
    
    # 1. መረጃው እንደ global መኖሩን አረጋግጥ
    if 'user_withdraw_data' not in globals():
        user_withdraw_data = {}
        
    user_id = message.chat.id
    bank_name = message.text.strip()
    
    # 2. ተጠቃሚው በእርግጥ Withdraw ን እየጀመረ መሆኑን ለመለየት 
    # በመጀመሪያ ተጠቃሚውን dictionary ውስጥ መፍጠር አለብህ
    if user_id not in user_withdraw_data:
        user_withdraw_data[user_id] = {}
     
    if "amount" not in user_withdraw_data[user_id]:
        user_withdraw_data[user_id]["amount"] = 0              
    # አሁን መረጃውን በሰላም ማስቀመጥ ትችላለህ
    user_withdraw_data[user_id]["bank"] = bank_name
    
    msg = "💳 የባንክ አካውንት (የስልክ ቁጥር) ያስገቡ:-"
    sent_msg = bot.send_message(user_id, msg)
    bot.register_next_step_handler(sent_msg, get_withdraw_account)

def get_withdraw_account(message):
    user_id = message.chat.id
    account_num = message.text.strip()
    
    if user_id not in user_withdraw_data: return
    user_withdraw_data[user_id]["account"] = account_num
    
    msg = "👤 የአካውንቱን ሙሉ ስም (የባለቤቱን ስም) ያስገቡ፦"
    sent_msg = bot.send_message(user_id, msg)
    bot.register_next_step_handler(sent_msg, finalize_withdrawal)

def finalize_withdrawal(message):
    user_id = message.chat.id
    holder_name = message.text.strip()
    
    if user_id not in user_withdraw_data: return
    
    w_data = user_withdraw_data[user_id]
    amount = w_data["amount"]
    bank = w_data["bank"]
    account = w_data["account"]
    username = message.from_user.username or "ተጫዋች"
    
    request_id = f"req_{int(time.time() * 1000)}"
    
    withdraw_payload = {
        "user_id": str(user_id),
        "username": username,
        "bank": bank,
        "account": str(account),
        "holder": holder_name,
        "amount": float(amount),
        "status": "pending",
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        db.reference(f'withdraw_requests/{request_id}').set(withdraw_payload)
        update_balance(user_id, -amount)
        
        bot.send_message(user_id, f"✅ የማውጫ ጥያቄዎ ተመዝግቧል!", reply_markup=get_main_menu(user_id))
        
        # አድሚን ጋር የሚላክ ሜሴጅ ከ Button ጋር
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ አጽድቅ", callback_data=f"approve_with_{request_id}"))
        
        bot.send_message(ADMIN_ID, f"🔔 አዲስ የዊዝድሮው ጥያቄ!\nተጫዋች: @{username}\nመጠን: {amount} ETB\nባንክ: {bank}\nአካውንት: {account}", reply_markup=markup)
    except Exception as e:
        print(f"❌ Withdraw Firebase Error: {e}")
        bot.send_message(user_id, "❌ ስህተት አጋጥሟል።")
        
    if user_id in user_withdraw_data:
        del user_withdraw_data[user_id]

# --- ⚡ 9. ራስ-ሰር ዲፖዚት ማፅደቂያ (Auto-Approve Engine) ---
# --- ⚡ 9. ራስ-ሰር ዲፖዚት ማፅደቂያ (Auto-Approve Engine) ---
def process_auto_deposit(snapshot_data):
    # 📌 ማስተካከያ 1፦ የመጣው ዳታ ባዶ ከሆነ ወይም dict ካልሆነ ቀጥታ እንዲመለስ ማድረግ
    if not snapshot_data or not isinstance(snapshot_data, dict):
        return

    for req_id, req in snapshot_data.items():
        # 📌 ማስተካከያ 2፦ እያንዳንዱ የጥያቄ መረጃ dict መሆኑን ማረጋገጥ ('int' ስህተትን ይከላከላል)
        if isinstance(req, dict):
            if req.get("status") == "pending" or "status" not in req:
                sms_body = req.get("body", "")
                user_id = req.get("userId")
                
                if not sms_body or not user_id:
                    continue

                amount_match = re.search(r'(?:ETB|credited with ETB|transferred ETB|amount)\s*([\d,.]+)', sms_body, re.IGNORECASE)
                
                if amount_match:
                    try:
                        amount_str = amount_match.group(1).replace(",", "")
                        amount = float(amount_str)
                        
                        print(f"💰 የተገኘ የዲፖዚት መጠን: {amount} ETB ለተጠቃሚ {user_id}")
                        
                        update_balance(user_id, amount)
                        _, new_balance = get_user_data(user_id)
                        
                        db.reference(f'deposit_requests/{req_id}').update({
                            "status": "approved",
                            "processed_amount": amount
                        })
                        
                        success_text = (
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"🔔 የተቀማጭ ገንዘብ ማሳወቂያ!\n"
                            f"━━━━━━━━━━━━━━━━━━\n\n"
                            f"💵 በባንክ የላኩት ገቢ መጠን: *{amount} ETB*\n"
                            f"✅ በተሳካ ሁኔታ በራስ-ሰር ጸድቆልዎታል።\n"
                            f"📈 አሁን ያለዎት ጠቅላላ የጌም ባላንስ: *{new_balance} ETB*\n\n"
                            f"የባንክ መልዕክትዎ በትክክል ተረጋግጧል። መልካም ጨዋታ! 🎯\n"
                            f"━━━━━━━━━━━━━━━━━━"
                        )
                        bot.send_message(user_id, success_text, parse_mode="Markdown", reply_markup=get_main_menu(user_id))
                        bot.send_message(ADMIN_ID, f"🔔 አውቶማቲክ ማሳወቂያ፦ ተጫዋች {user_id} የላከው የ {amount} ETB ዲፖዚት በሲስተሙ ራሱ ጸድቋል።")
                    except Exception as inner_e:
                        print(f"❌ Error parsing amount inside auto deposit: {inner_e}")

def check_firebase_deposits_loop():
    while True:
        try:
            response = requests.get(f"{FIREBASE_URL}/deposit_requests.json")
            if response.status_code == 200:
                data = response.json()
                # 📌 ማስተካከያ 3፦ ዳታው መኖሩን እና በትክክል dictionary መሆኑን ማረጋገጥ
                if data and isinstance(data, dict):
                    process_auto_deposit(data)
        except Exception as e:
            # 📌 ማስተካከያ 4፦ ትክክለኛውን የሲስተም ስህተት በግልጽ ማተም (የምን ችግር እንደሆነ ለማወቅ)
            print(f"❌ Firebase ሪኩዌስት ስህተት፦ {e}")
        time.sleep(3)

threading.Thread(target=check_firebase_deposits_loop, daemon=True).start()

# --- 10. SMS Logic & Manual Copy-Paste Backup ---
received_sms_cache = {}

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.chat.id
    text = message.text.strip()

    # 1. አዝራሮችን መለየት (Menu Buttons)
    if text == "Play":
        # Play አዝራር ሲጫን ምን ይደረግ?
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🕹️ ጨዋታውን ይጀምሩ", web_app=WebAppInfo(url=WEB_APP_URL)))
        bot.send_message(user_id, "በታች ያለውን ቁልፍ በመጫን ጨዋታውን ይጀምሩ፦", reply_markup=markup)
        return

    elif text == "Balance":
        _, balance = get_user_data(user_id)
        bot.send_message(user_id, f"💳 አሁን ያለዎት ባላንስ፦ {balance} ETB")
        return

    elif text == "Register":
        return fast_reg(message)

    elif text == "Deposit":
        start_deposit(message)
        return

    elif text == "Withdraw":
        bot.send_message(user_id, "💸 ለመውጣት ይሄንን ይጫኑ፦", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("💸 Withdraw", callback_data="with_start")))
        return

    elif text == "Invite":
        bot.send_message(user_id, "ጓደኞችዎን በዚህ ሊንክ ይጋብዙ፦ https://t.me/Aradeyebot")
        return

    tids_found = re.findall(r'\b(?:DEM|FT)[A-Z0-9]{8,12}\b', text, re.IGNORECASE)
    amount_match = re.search(r'(?:ETB|ብር|credited with ETB|amount)\s*([\d+(?:\.\d+)?]+)', text, re.IGNORECASE)

    # Pre-define match checks to avoid UnboundLocalError
    tele_tid_match = re.search(r'\b(TXN\d+)\b', text)
    cbe_tid_match = re.search(r'\b(FT\d+)\b', text)

    if amount_match and tids_found:
        amount = float(amount_match.group(1))
        tids_to_save = [tid.upper() for tid in tids_found]

        for tid in tids_to_save:
            received_sms_cache[tid] = amount
            
        try:
            main_tid = tids_to_save[0]
            tid_ref = db.reference(f'used_tids/{main_tid}')
            tid_status = tid_ref.get()
            
            if tid_status is not None:
                bot.reply_to(message, "❌ የተከለከለ ተግባር!\nይህ የግብይት መለያ ቁጥር (TID) ቀድሞ ጥቅም ላይ ውሏል (Expired ሆኗል)።")
                return

            db_ref = db.reference(f'users/{user_id}')
            user_data = db_ref.get()
            
            current_balance = 0.0
            if user_data and 'balance' in user_data:
                current_balance = float(user_data['balance'])
            
            new_balance = current_balance + amount
            db_ref.update({'balance': new_balance})
            update_balance(user_id, amount)
            
            tid_ref.set({
                'used_by': user_id,
                'amount': amount,
                'time': time.time()
            })
            
            bot.reply_to(message, f"✅ ክፍያዎ በተሳካ ሁኔታ ተረጋግጧል!\n📥 የተጨመረ: {amount} ETB\n💳 የአሁን ሂሳብዎ (Balance): {new_balance} ETB")
            return
            
        except Exception as e:
            bot.reply_to(message, f"❌ ስህተት አጋጥሟል: {str(e)}")
            return

    matched_tid = None
    if tele_tid_match and tele_tid_match.group(1) in received_sms_cache:
        matched_tid = tele_tid_match.group(1)
    elif cbe_tid_match and cbe_tid_match.group(0) in received_sms_cache:
        matched_tid = cbe_tid_match.group(0)
    elif text in received_sms_cache:
        matched_tid = text

    if matched_tid:
        deposit_amount = received_sms_cache[matched_tid]
        update_balance(user_id, deposit_amount)
        _, new_total_balance = get_user_data(user_id)
        
        for k, v in list(received_sms_cache.items()):
            if v == deposit_amount:
                del received_sms_cache[k]
                
        success_msg = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ የሂሳብ መሙላት ተሳክቷል!\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 የገባው ዲፖዚት፦ +{deposit_amount} ETB\n"
            f"💳 አጠቃላይ ሂሳብዎ፦ {new_total_balance} ETB\n\n"
            f"የላኩት መለያ ቁጥር ({matched_tid}) በትክክል ተረጋግጧል።\n"
            f"አሁን ወደ ዋናው ገጽ በመመለስ መጫወት ይችላሉ! 🕹️\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(user_id, success_msg, parse_mode="Markdown", reply_markup=get_main_menu(user_id))
        bot.send_message(ADMIN_ID, f"🔔 ማሳወቂያ፦ ተጫዋች {user_id} በ TID {matched_tid} መጠን {deposit_amount} ETB በተሳካ ሁኔታ አካውንቱ ላይ ደምሯል።")
        return
    else:
        if len(text) >= 10 or tele_tid_match or cbe_tid_match:
            bot.send_message(user_id, "❌ የላኩት መለያ ቁጥር (TID) በሲስተሙ አልተገኘም ወይም ቀድሞ ጥቅም ላይ ውሏል። እባክዎ በትክክል መጻፍዎን ያረጋግጡ።")
            return

    if not text.startswith('/'):
            bot.send_message(user_id, "ትክክለኛ ትዕዛዝ አይደለም። እባክዎ ከታች ያሉትን ቁልፎች ይጠቀሙ。", reply_markup=get_main_menu(user_id))

# ቦቶችን ለማስወገድ እና የተመረጡ ቁጥሮችን ብቻ ለመያዝ
def validate_and_save_numbers(user_id, numbers):
    # ቁጥሮች ከ1-500 መሆናቸውን በServer በኩል እንደገና ማረጋገጥ (Security)
    if all(1 <= n <= 500 for n in numbers) and len(numbers) <= 3:
        db.reference(f'liveGame/selectedCards/{user_id}').set({
            'numbers': numbers,
            'status': 'confirmed'
        })
    else:
        print("🛑 የተሳሳተ ቁጥር ተልኳል!")#
# ይህንን ፋንክሽን ከሌሎች ፋንክሽኖች ጋር (ለምሳሌ ከ handle_text በታች) ያስገቡ
def start_deposit(message):
    user_id = message.chat.id
    # የባንክ መረጃዎችን የያዘ መልዕክት
    msg = (
        "🏦 *የባንክ ተቀማጭ ሂደት*\n\n"
        "እባክዎ ከታች ባሉት አካውንቶች ብር ያስገቡ፦\n\n"
        "• 🏦 ንግድ ባንክ (CBE)፦ `1000525826396`\n"
        "  👤 ስም፦ Amanuel Zewdu\n\n"
        "• 📱 ቴሌብር (telebirr)፦ `0910564117`\n"
        "  👤 ስም፦ Amanuel Zewdu\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "ብር ካስገቡ በኋላ የባንክ መልዕክቱን (SMS) ኮፒ አድርገው እዚህ ላይ ፔስት (Paste) ያድርጉ።\n"
        "⚠️ ሲስተማችን የላኩትን መረጃ ወዲያውኑ ያረጋግጣል።"
    )
    # parse_mode="Markdown" ስላለው በውስጡ ያሉትን ኮከቦች (*) የፊደል ቅርጽ ለመቀየር ይጠቀማል
    sent_msg = bot.send_message(user_id, msg, parse_mode="Markdown")
    
    # ተጠቃሚው የሚመልሰውን መልዕክት ለመቀበል ይዘጋጃል
    bot.register_next_step_handler(sent_msg, process_deposit_sms)

def process_deposit_sms(message):
    user_id = message.chat.id
    sms_text = message.text
    
    # 1. የባንክ SMS መሆኑን ለማረጋገጥ (Validation)
    # እዚህ ላይ የራስህን የባንክ አካውንት ቁጥሮች አስገባ
    if "1000525826396" not in sms_text and "0910564117" not in sms_text:
        bot.send_message(user_id, "❌ ስህተት! ይህ ትክክለኛ የባንክ መልዕክት (SMS) አይደለም። እባክዎ በትክክለኛው የባንክ አካውንት ብር መላክዎን ያረጋግጡ።")
        return

    # 2. ቀደም ብሎ ተልኳል ወይ? (Duplicate check)
    ref = db.reference('deposit_requests')
    existing_data = ref.order_by_child('body').equal_to(sms_text).get()
    
    if existing_data:
        bot.send_message(user_id, "⚠️ ይህ የባንክ መልዕክት ቀደም ብሎ ጥቅም ላይ ውሏል!")
        return

    # 3. መረጃውን ወደ Firebase መላክ
    deposit_data = {
        "userId": user_id,
        "body": sms_text,
        "status": "pending",
        "timestamp": time.time()
    }
    
    ref.push(deposit_data)
    bot.send_message(user_id, "✅ መረጃዎ ተቀብለናል! ሲስተማችን እያረጋገጠ ነው፣ ትንሽ ይጠብቁ...")
# መስመር 707 ላይ የሚጻፍ አዲስ ኮድ
@bot.message_handler(func=lambda message: message.text == "Register")
def register_user(message):
    user_id = message.chat.id
    
    # ተጠቃሚው ቀድሞ መመዝገቡን ማረጋገጥ
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        bot.send_message(user_id, "ይቅርታ! ቦነሱን አስቀድመው ወስደዋል፣ በድጋሚ መስጠት አይቻልም።")
    else:
        # አዲስ ተጠቃሚ ሲመዘገብ 20 ብር ብቻ እንዲያገኝ
        cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 20.0))
        conn.commit()
        bot.send_message(user_id, "እንኳን ደስ አለዎት! 20 ብር ቦነስ ተቀብለዋል።")
        # ስልክ ቁጥር የሚጠይቀውን ፋንክሽን ጥራ
        fast_reg(message)
def fast_reg(message):
    user_id = message.chat.id
    
    # ስልክ ቁጥርን የሚጠይቅ አዝራር (Contact Request)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📱 ስልክ ቁጥርህን አጋራ", request_contact=True))
    
    msg = "እንኳን ወደ Jobe Bingo በደህና መጡ! ለመመዝገብ ከታች ያለውን «📱 ስልክ ቁጥርህን አጋራ» የሚለውን ቁልፍ ይጫኑ።"
    bot.send_message(user_id, msg, reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact:
        # 1. ስልክ ቁጥሩን አስቀምጥ
        save_phone(message.chat.id, message.contact.phone_number)
        
        # 2. የድሮውን ኪቦርድ ለማስወገድ ReplyKeyboardRemove() ይጠቀሙ
        bot.send_message(message.chat.id, "✅ በስኬት ተመዝግበዋል!", reply_markup=ReplyKeyboardRemove())
        
        # 3. ዋናውን ሜኑ መልሰህ ላክ (ይህ አዲስ ኪቦርድ ያሳያል)
        # እዚህ ጋር የምትጠቀመውን ሜኑ ሰሪ ፋንክሽን (ለምሳሌ get_main_menu ከሆነ) ጥራው
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Register"), KeyboardButton("Play"))
        markup.add(KeyboardButton("Balance"), KeyboardButton("Deposit"))
        markup.add(KeyboardButton("Withdraw"), KeyboardButton("Invite"))
        
        bot.send_message(message.chat.id, "ለመቀጠል ከታች ያለውን ሜኑ ይጠቀሙ፦", reply_markup=markup)

# --- 11. Balance & Deposit Handlers ---
@bot.callback_query_handler(func=lambda call: call.data == "bal")
def check_balance(call):
    user_id = call.message.chat.id
    _, balance = get_user_data(user_id)
    
    msg = f"━━━━━━━━━━━━━━\n💳 ያለዎት ሂሳብ (Balance)\n━━━━━━━━━━━━━━\n💰 {balance} ETB"
    if balance < 10:
        msg += "\n\n⚠️ ማሳሰቢያ፦ ሂሳብዎ ዝቅተኛ ስለሆነ እባክዎ በ 'Deposit' በኩል ይሙሉ!"
    
    bot.answer_callback_query(call.id)
    bot.send_message(user_id, msg)

@bot.callback_query_handler(func=lambda call: call.data == "dep")
def deposit_amount_menu(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    msg = (
        "💰 የሂሳብ መሙያ ገጽ (Deposit)\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1. በነዚህ የባንክ አካውንቶች ብር ያስገቡ፦\n"
        "   • 🏦 ንግድ ባንክ (CBE)፦ 1000525826396\n"
        "     👤 ስም፦ Amanuel Zewdu\n\n"
        "   • 📱 👑 ቴሌብር (telebirr)፦ 0910564117\n"
        "     👤 ስም፦ Amanuel Zewdu\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "2. ብር ካስገቡ በኋላ ከባንክ የደረሰዎትን መልዕክት ሙሉ በሙሉ ኮፒ (Copy) አድርገው እዚህ ላይ ፔስት (Paste) ያድርጉት。\n\n"
        "⚠️ ማሳሰቢያ፦ ሲስተሙ የላኩትን ቁጥር ከባንክ መልዕክት ጋር አመሳክሮ በሰከንዶች ውስጥ ሂሳብዎ ላይ ይጨምርልዎታል።"
    )
    
    markup = InlineKeyboardMarkup(row_width=3)
    btn30 = InlineKeyboardButton("💰 30 ETB", callback_data="amt_30")
    btn50 = InlineKeyboardButton("💰 50 ETB", callback_data="amt_50")
    btn100 = InlineKeyboardButton("💎 100 ETB", callback_data="amt_100")
    btn200 = InlineKeyboardButton("💎 200 ETB", callback_data="amt_200")
    btn500 = InlineKeyboardButton("🔥 500 ETB", callback_data="amt_500")
    btn1000 = InlineKeyboardButton("👑 1000 ETB", callback_data="amt_1000")
    
    btn_custom = InlineKeyboardButton("✍️ በራሴ ሌላ መጠን ለመጻፍ", callback_data="amt_custom")
    btn_back = InlineKeyboardButton("🔙 ወደ ዋና ሜኑ ተመለስ", callback_data="back_to_main")
    
    markup.add(btn30, btn50, btn100)
    markup.add(btn200, btn500, btn1000)
    markup.add(btn_custom)
    markup.add(btn_back)
    
    bot.edit_message_text(msg, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
    except:
        pass
    bot.send_message(user_id, "🕹️ Jobe Bingo Bot ዋና ማውጫ", reply_markup=get_main_menu(user_id))

@bot.message_handler(func=lambda message: message.text == "Invite")
def invite_user(message):
    user_id = message.chat.id
    # የቦትህን ሊንክ እዚህ ቦታ ላይ አስገባ (አሁን ያለው ምሳሌ ነው)
    bot_link = "https://t.me/Aradeyebot" 
    
    msg = (
        "📢 *ጓደኞችዎን ይጋብዙ!*\n\n"
        "ይህንን ሊንክ በመላክ ጓደኞችዎን ወደ ጆቤ ቢንጎ ይጋብዙ፦\n\n"
        f"`{bot_link}`\n\n"
        "⚠️ እያንዳንዱ የተጋበዘ ሰው ሲመዘገብ የጉርሻ (Bonus) ሽልማት ያገኛሉ!"
    )
    
    bot.send_message(user_id, msg, parse_mode="Markdown")

        
# ይህንን ኮድ ከፋይልህ መጨረሻ ላይ አስገባ
# ቴሌግራም ቦት ከመጀመሩ በፊት
if __name__ == "__main__":
    # የጨዋታውን ሂደት በተለየ Thread አስጀምር
    game_thread = threading.Thread(target=start_bingo_numbers, daemon=True)
    game_thread.start()
    
    # የቴሌግራም ቦቱን አስጀምር
    print("🤖 የቴሌግራም ቦት እየሰራ ነው...")
    bot.infinity_polling()
