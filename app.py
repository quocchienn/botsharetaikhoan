import telebot
from telebot import types
from pymongo import MongoClient
from datetime import datetime, date
import random
import threading
import time
import os  # Thêm os để lấy env variables trên Render

# ================== CẤU HÌNH TỪ ENVIRONMENT VARIABLES (AN TOÀN CHO RENDER) ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Lấy từ Render Environment
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "free_share_bot")  # Có thể thay đổi tên DB nếu cần

if not BOT_TOKEN or not MONGO_URI:
    raise ValueError("Vui lòng thiết lập BOT_TOKEN và MONGO_URI trong Environment Variables trên Render!")

ADMIN_ID = 5589888565  # Có thể chuyển thành env nếu cần: int(os.getenv("ADMIN_ID", "0"))

# ================== DANH SÁCH TÀI KHOẢN FREE ==================

FREE_ACCOUNTS = {
    "capcut": {
        "name": "CapCut Pro Free",
        "emoji": "🎬",
        "accounts": [
            "bảo trì ",
            # Thêm nhiều càng tốt → bot sẽ random 1 cái
        ]
    },
    "chatgpt": {
        "name": "ChatGPT Shared",
        "emoji": "🤖",
        "accounts": [
            "bảo trì",
        ]
    },
    "canva": {
        "name": "Canva Pro Teams Free",
        "emoji": "🎨",
        "accounts": [
            "Invite link: https://www.canva.com/brand/join?token=F8CsC2hexK3B8JRVWWOzeg&referrer=team-invite",
        ]
    },
    "netflix": {
        "name": "Netflix Shared",
        "emoji": "📺",
        "accounts": [
            "bảo trì",
        ]
    },
}

# ================== KHỞI TẠO ==================

bot = telebot.TeleBot(BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]
users_collection = db.users

# ================== HÀM HỖ TRỢ ==================

def can_user_take_today(user_id, service_key):
    """Kiểm tra user còn lượt lấy hôm nay không (tối đa 2 lần/dịch vụ)"""
    today = date.today().isoformat()
    record = users_collection.find_one({
        "user_id": user_id,
        "service": service_key,
        "date": today
    })
    if record is None:
        return True
    return record.get("count", 0) < 2

def mark_user_taken(user_id, service_key):
    """Tăng số lần lấy hôm nay và trả về số lần hiện tại"""
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
    kb = types.InlineKeyboardMarkup(row_width=2)
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
            pass  # Bỏ qua lỗi (quyền, tin nhắn đã xóa...)
    threading.Thread(target=delete, daemon=True).start()

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for key in FREE_ACCOUNTS:
        service = FREE_ACCOUNTS[key]
        kb.add(f"{service['emoji']} {service['name']}")
    return kb

# ================== /start ==================

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "🎉 <b>CHÀO MỪNG BẠN ĐẾN SHARE TÀI KHOẢN FREE</b>\n\n"
        "🔥 Chia sẻ tài khoản Pro/Teams miễn phí!\n\n"
        "⚠️ <i>Quy định:</i>\n"
        "• Mỗi ngày được lấy <b>tối đa 2 tài khoản</b> cho mỗi dịch vụ\n"
        "• Mỗi lần nhận <b>1 tài khoản ngẫu nhiên</b>\n"
        "❤️ Dùng hợp lý, không đổi pass nhé!\n\n"
        "👇 Chọn dịch vụ hoặc dùng /taikhoan trong nhóm!",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ================== LỆNH /taikhoan ==================

@bot.message_handler(commands=["taikhoan"])
def taikhoan_command(msg):
    menu_msg = bot.send_message(
        msg.chat.id,
        "📋 <b>Chọn dịch vụ để nhận 1 tài khoản free</b>\n"
        "(Mỗi ngày tối đa 2 lần mỗi dịch vụ)\n\n"
        "⏳ <i>Menu này sẽ tự xóa sau 15 giây trong nhóm</i>",
        parse_mode="HTML",
        reply_markup=inline_service_menu()
    )
    
    if msg.chat.type in ["group", "supergroup"]:
        delete_message_later(msg.chat.id, menu_msg.message_id, delay=15)

# ================== XỬ LÝ INLINE BUTTON ==================

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
            f"⛔ Hôm nay bạn đã lấy đủ 2 lần {service['name']} rồi!\nNgày mai quay lại nhé ❤️",
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
        f"📊 <b>Bạn đã lấy {current_count}/2 lần hôm nay</b>\n"
        f"🔄 Ngày mai reset lại 2 lần mới!"
    )
    
    try:
        bot.send_message(user_id, text, parse_mode="HTML")
        bot.answer_callback_query(call.id, f"✅ Đã gửi tài khoản (lần {current_count}/2)!", show_alert=False)
    except:
        bot.answer_callback_query(call.id, "❌ Vui lòng /start bot riêng để nhận!", show_alert=True)

# ================== MENU CHÍNH (REPLY KEYBOARD) ==================

@bot.message_handler(func=lambda m: any(service['emoji'] in m.text and service['name'] in m.text for service in FREE_ACCOUNTS.values()))
def send_free_account(msg):
    user_id = msg.from_user.id
    selected_key = None
    
    for key, service in FREE_ACCOUNTS.items():
        if service['emoji'] in m.text and service['name'] in m.text:
            selected_key = key
            break
    
    if not selected_key:
        return
    
    service = FREE_ACCOUNTS[selected_key]
    
    if not can_user_take_today(user_id, selected_key):
        bot.send_message(
            msg.chat.id,
            f"⛔ <b>Bạn đã lấy đủ 2 lần {service['name']} hôm nay rồi!</b>\n\n"
            f"Quay lại ngày mai để nhận thêm nhé ❤️",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        return
    
    account = get_one_random_account(selected_key)
    if not account:
        bot.send_message(msg.chat.id, f"❌ Hiện chưa có tài khoản cho {service['name']}.", reply_markup=main_menu())
        return
    
    current_count = mark_user_taken(user_id, selected_key)
    
    text = (
        f"{service['emoji']} <b>BẠN NHẬN ĐƯỢC 1 TÀI KHOẢN!</b>\n\n"
        f"<b>Dịch vụ:</b> {service['name']}\n"
        f"<b>Tài khoản:</b>\n<code>{account}</code>\n\n"
        f"✅ Chúc sử dụng vui vẻ!\n"
        f"📊 <b>Bạn đã lấy {current_count}/2 lần hôm nay</b>\n"
        f"🔄 Ngày mai reset lại 2 lần mới nhé!"
    )
    
    bot.send_message(msg.chat.id, text, parse_mode="HTML", reply_markup=main_menu())

# ================== CHẠY BOT ==================

if __name__ == "__main__":
    print("🤖 Bot Share Tài Khoản Free đang khởi động trên Render...")
    print("Tối đa 2 lần/ngày/dịch vụ | Menu /taikhoan tự xóa sau 15s")
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"Lỗi nghiêm trọng: {e}")
        time.sleep(10)  # Thử lại sau 10s nếu lỗi
