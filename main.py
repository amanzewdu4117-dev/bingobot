import telebot
from telebot import types

TOKEN = "የአንተ_ቦት_ቶከን_እዚህ_ይግባ"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    # url የሚለው ቦታ ላይ በኋላ Netlify ላይ የምናገኘውን ሊንክ እናስገባለን
    web_info = types.WebAppInfo(url="https://amanzewdu4117-dev.github.io/bingobot/")
    button = types.InlineKeyboardButton(text="ቢንጎ ተጫወት 🎮", web_app=web_info)
    markup.add(button)
    
    bot.send_message(message.chat.id, "እንኳን ደህና መጡ! ጨዋታውን ለመጀመር ከታች ያለውን በተን ይጫኑ።", reply_markup=markup)

print("ቦቱ እየሰራ ነው...")
bot.polling()
