import telebot
from telebot import types
from pymongo import MongoClient
from datetime import datetime, date
import random
import threading
import time
import os
from flask import Flask

# ================== CẤU HÌNH ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "free_share_bot")

if not BOT_TOKEN or not MONGO_URI:
    raise ValueError("Thiết lập BOT_TOKEN và MONGO_URI trong Environment Variables!")

# ================== DANH SÁCH TÀI KHOẢN FREE VỚI KEYWORDS ==================

FREE_ACCOUNTS = {
    "capcut": {
        "name": "CapCut Pro Free",
        "emoji": "🎬",
        "keywords": ["capcut", "cap", "cut", "cap cut"],
        "accounts": [
            "Email: hocey76005@m3player.com | Pass: Chien2007",
            "Email: xadas61730@m3player.com | Pass: Chien2k5",
            "Email: fajic10847@m3player.com | Pass: Freecamdoihoi",
            "Email: wilber22mjg0bl83@hunght1890.com | Pass: a123456",
    "Email: fredy.rath2mjg0bjj5@hunght1890.com | Pass: a123456",
    "Email: houston_jacomjhfyx4u@hunght1890.com | Pass: a123456",
    "Email: savanah_olsomjhfyeja@hunght1890.com | Pass: a123456",
    "Email: maureen_dibbmjhfyx7x@hunght1890.com | Pass: a123456",
    "Email: barney.kutchmjhfyea3@hunght1890.com | Pass: a123456",
    "Email: elmo.graham2mjhfxocw@hunght1890.com | Pass: a123456",
    "Email: tate.howell9mjhfxm9q@hunght1890.com | Pass: a123456",
    "Email: tatum_stiedemjhfxngn@hunght1890.com | Pass: a123456",
    "Email: fay_gerlachmjhfxn8u@hunght1890.com | Pass: a123456",
    "Email: daija.rempelmjhfyxlv@hunght1890.com | Pass: a123456",
    "Email: carrie.mayermjf5tirj@hunght1890.com | Pass: a123456",
    "Email: madonna_swifmjf5tjcj@hunght1890.com | Pass: a123456",
    "Email: lauretta.emmmjf44k0g@hunght1890.com | Pass: a123456",
    "Email: eveline_goodmjf5thna@hunght1890.com | Pass: a123456",
    "Email: buster_torp1mjf5tho6@hunght1890.com | Pass: a123456",
    "Email: major_boyle1mjf5timc@hunght1890.com | Pass: a123456",
    "Email: ursula.raumjf44jjh@hunght1890.com | Pass: a123456",
    "Email: anya2mjf44jcj@hunght1890.com | Pass: a123456",
    "Email: jillian_waelmjf9fimu@hunght1890.com | Pass: a123456",
    "Email: eliezer40mjf9fknl@hunght1890.com | Pass: a123456",
    "Email: aditya_ebertmjf9jf0f@hunght1890.com | Pass: a123456",
    "Email: dave.bartolemjf9i4e5@hunght1890.com | Pass: a123456",
    "Email: casandra.mclmjf9i4rv@hunght1890.com | Pass: a123456",
    "Email: breana.moscimjf9jdvs@hunght1890.com | Pass: a123456",
    "Email: sandy_schmitmjf9jeaa@hunght1890.com | Pass: a123456",
    "Email: chesley_davimjf9jdgy@hunght1890.com | Pass: a123456",
    "Email: finn.robertsmjf44iyq@hunght1890.com | Pass: a123456",
    "Email: chelsey.nikomjf9i4nj@hunght1890.com | Pass: a123456",
    "Email: annette11mjf9k9am@hunght1890.com | Pass: a123456",
        ]
    },
    "chatgpt": {
        "name": "ChatGPT PLus",
        "emoji": "🤖",
        "keywords": ["chatgpt", "gpt", "chat gpt", "ai"],
        "accounts": [
         "accounts": [
    "Email: rorekay973@gamintor.com | Pass: quocchienv2123",
    "Email: fafovid463@gamintor.com | Pass: quocchien273162",
    "Email: cebaxa7188@m3player.com | Pass: quocchien741210",
    "Email: jahiw31399@m3player.com | Pass: quocchien170121",
    "Email: bemohi4340@gamintor.com | Pass: quocchien723140",
    # Bạn có thể thêm nhiều hơn nếu có
],
    },
    "canva": {
        "name": "Canva Pro Teams Free",
        "emoji": "🎨",
        "keywords": ["canva", "design", "thietke", "can va"],
        "accounts": [
            "Invite link: https://www.canva.com/brand/join?token=F8CsC2hexK3B8JRVWWOzeg&referrer=team-invite",
        ]
    },
    "netflix": {
        "name": "Netflix Shared",
        "emoji": "📺",
        "keywords": ["netflix", "nf", "phim", "net flix"],
        "accounts": [
            "Email: firstmail640@gmail10p.com | Pass: GHAX12170",
        ]
    },
}
# ================== KHỞI TẠO ==================

bot = telebot.TeleBot(BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]
users_collection = db.users

# ================== FLASK SERVER ==================

app = Flask(__name__)

@app.route('/')
def health_check():
    return "🤖 Bot Share Tài Khoản Free đang chạy khỏe mạnh! 🚀", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ================== HÀM HỖ TRỢ ==================

def can_user_take_today(user_id, service_key):
    today = date.today().isoformat()
    record = users_collection.find_one({
        "user_id": user_id,
        "service": service_key,
        "date": today
    })
    if record is None:
        return True
    return record.get("count", 0) < 5

def mark_user_taken(user_id, service_key):
    today = date.today().isoformat()
    result = users_collection.find_one_and_update(
        {"user_id": user_id, "service": service_key, "date": today},
        {"$inc": {"count": 1}, "$setOnInsert": {"taken_at": datetime.now()}},
        upsert=True,
        return_document=True
    )
    return result.get("count", 1)

def get_one_random_account(service_key):
    accounts = FREE_ACCOUNTS[service_key]["accounts"]
    return random.choice(accounts) if accounts else None

def inline_service_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, service in FREE_ACCOUNTS.items():
        kb.add(types.InlineKeyboardButton(
            text=f"{service['emoji']} {service['name']}",
            callback_data=f"get_{key}"
        ))
    return kb

def delete_message_later(chat_id, message_id, delay=15):
    def delete():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delete, daemon=True).start()

# ================== /start ==================

@bot.message_handler(commands=["start"])
def start(msg):
    welcome_text = (
        "🎉 <b>CHÀO MỪNG BẠN ĐẾN SHARE TÀI KHOẢN FREE</b>\n\n"
        "🔥 Chia sẻ tài khoản Pro/Teams miễn phí!\n\n"
        "⚠️ <i>Quy định:</i>\n"
        "• Mỗi ngày được lấy <b>tối đa 5 lần</b> cho mỗi dịch vụ\n"
        "• Mỗi lần nhận <b>1 tài khoản ngẫu nhiên</b>\n"
        "❤️ Dùng hợp lý, không đổi pass nhé!\n\n"
        "👇 Chọn dịch vụ để nhận ngay!\n"
        "<i>Gõ capcut, chatgpt, canva, netflix để mở menu nhanh</i>"
    )
    
    bot.send_message(
        msg.chat.id,
        welcome_text,
        parse_mode="HTML",
        reply_markup=inline_service_menu()
    )

# ================== /taikhoan ==================

@bot.message_handler(commands=["taikhoan"])
def taikhoan_command(msg):
    menu_text = (
        "📋 <b>Chọn dịch vụ để nhận 1 tài khoản free</b>\n"
        "(Mỗi ngày tối đa 5 lần mỗi dịch vụ)\n\n"
        "⏳ <i>Menu này sẽ tự xóa sau 15 giây</i>"
    )
    
    menu_msg = bot.send_message(
        msg.chat.id,
        menu_text,
        parse_mode="HTML",
        reply_markup=inline_service_menu()
    )
    
    if msg.chat.type in ["group", "supergroup"]:
        delete_message_later(msg.chat.id, menu_msg.message_id, delay=15)

# ================== XỬ LÝ TỪ KHÓA NGẮN ==================

@bot.message_handler(func=lambda m: True)
def handle_keyword(msg):
    text = msg.text.lower().strip()
    selected_key = None
    
    for key, service in FREE_ACCOUNTS.items():
        if any(kw in text for kw in service["keywords"]):
            selected_key = key
            break
    
    if not selected_key:
        return
    
    menu_text = (
        f"🔥 <b>Bạn muốn nhận {FREE_ACCOUNTS[selected_key]['name']}?</b>\n"
        f"(Mỗi ngày tối đa 5 lần)\n\n"
        f"👇 Chọn dịch vụ bên dưới để nhận ngay!"
    )
    
    menu_msg = bot.send_message(
        msg.chat.id,
        menu_text,
        parse_mode="HTML",
        reply_markup=inline_service_menu()
    )
    
    if msg.chat.type in ["group", "supergroup"]:
        delete_message_later(msg.chat.id, menu_msg.message_id, delay=15)

# ================== XỬ LÝ INLINE ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("get_"))
def handle_inline_get(call):
    user_id = call.from_user.id
    service_key = call.data.split("_")[1]
    
    if service_key not in FREE_ACCOUNTS:
        bot.answer_callback_query(call.id, "❌ Dịch vụ không tồn tại!", show_alert=True)
        return
    
    service = FREE_ACCOUNTS[service_key]
    
    if not can_user_take_today(user_id, service_key):
        bot.answer_callback_query(
            call.id,
            f"⛔ Hôm nay bạn đã lấy đủ 5 lần {service['name']} rồi!\nNgày mai quay lại nhé ❤️",
            show_alert=True
        )
        return
    
    account = get_one_random_account(service_key)
    if not account:
        bot.answer_callback_query(call.id, "❌ Hiện chưa có tài khoản cho dịch vụ này!", show_alert=True)
        return
    
    current_count = mark_user_taken(user_id, service_key)
    
    text = (
        f"{service['emoji']} <b>BẠN ĐÃ NHẬN THÀNH CÔNG!</b>\n\n"
        f"<b>Dịch vụ:</b> {service['name']}\n"
        f"<b>Tài khoản:</b>\n<code>{account}</code>\n\n"
        f"✅ Dùng hợp lý nhé!\n"
        f"📊 <b>Bạn đã lấy {current_count}/5 lần hôm nay</b>\n"
        f"🔄 Ngày mai reset lại 5 lần mới!"
    )
    
    try:
        bot.send_message(user_id, text, parse_mode="HTML")
        bot.answer_callback_query(call.id, f"✅ Đã gửi (lần {current_count}/5)!", show_alert=False)
    except:
        bot.answer_callback_query(call.id, "❌ Vui lòng chat riêng với bot để nhận!", show_alert=True)

# ================== CHẠY BOT + FLASK ==================

if __name__ == "__main__":
    print("🤖 Bot Share Tài Khoản Free đang khởi động...")
    print("Gõ capcut, chatgpt, canva, netflix → hiện menu inline (tự xóa 15s trong nhóm)")
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"Lỗi bot: {e}")
        time.sleep(10)
