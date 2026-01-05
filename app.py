import telebot
from telebot import types
from pymongo import MongoClient
from datetime import datetime, date
import random
import threading
import time
import os
from flask import Flask
from telebot.apihelper import ApiTelegramException

# ================== CẤU HÌNH ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "free_share_bot")

if not BOT_TOKEN or not MONGO_URI:
    raise ValueError("Thiết lập BOT_TOKEN và MONGO_URI trong Environment Variables!")

ADMIN_ID = 5589888565  # ID admin duy nhất của bạn

# ================== DANH SÁCH TÀI KHOẢN FREE (BẮT ĐẦU RỖNG - SẼ ĐƯỢC CẬP NHẬT BẰNG FILE TXT) ==================

FREE_ACCOUNTS = {
    "capcut": {
        "name": "CapCut Pro",
        "emoji": "🎬",
        "keywords": ["capcut", "cap", "cut", "cap cut"],
        "accounts": []
    },
    "chatgpt": {
        "name": "ChatGPT Plus",
        "emoji": "🤖",
        "keywords": ["chatgpt", "gpt", "chat gpt", "ai"],
        "accounts": []
    },
    "canva": {
        "name": "Canva Pro Teams Free",
        "emoji": "🎨",
        "keywords": ["canva", "design", "thietke", "can va"],
        "accounts": []
    },
    "netflix": {
        "name": "Netflix Shared",
        "emoji": "📺",
        "keywords": ["netflix", "nf", "phim", "net flix"],
        "accounts": []
    },
    "picsart": {
        "name": "Picsart Gold",
        "emoji": "🖼️",
        "keywords": ["picsart", "pic", "pics art", "edit anh", "chinh anh"],
        "accounts": []
    },
    "hma": {
        "name": "HMA VPN Pro",
        "emoji": "🔒",
        "keywords": ["hma", "vpn", "hide my ass", "hidemyass", "proxy"],
        "accounts": []
    },
}

# Biến lưu trạng thái admin đang cập nhật tài khoản
admin_update_state = {}  # {admin_id: {"file_id": file_id}}

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
    return record.get("count", 0) < 10

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
    if not accounts:
        return None
    return random.choice(accounts)

def get_remaining_count(service_key):
    count = len(FREE_ACCOUNTS.get(service_key, {}).get("accounts", []))
    if count == 0:
        return "🔴 Hết hàng"
    elif count <= 5:
        return f"🟡 Còn: {count} (Sắp hết)"
    else:
        return f"🟢 Còn: {count}"

def inline_service_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, service in FREE_ACCOUNTS.items():
        remaining = get_remaining_count(key)
        if "Hết hàng" in remaining:
            continue
        kb.add(types.InlineKeyboardButton(
            text=f"{service['emoji']} {service['name']} | {remaining}",
            callback_data=f"get_{key}"
        ))
    return kb

def get_today_stats():
    today = date.today().isoformat()
    stats = []
    total_taken = 0
    for key, service in FREE_ACCOUNTS.items():
        taken = users_collection.count_documents({"service": key, "date": today})
        remaining = get_remaining_count(key)
        stats.append(f"{service['emoji']} {service['name']}: {remaining} | <b>{taken} người lấy</b>")
        total_taken += taken
    stats_text = "\n".join(stats)
    return f"📊 <b>THỐNG KÊ & TỒN KHO HÔM NAY</b>\n{stats_text}\n\n💥 <b>Tổng lượt lấy: {total_taken}</b>"

def delete_message_later(chat_id, message_id, delay=15):
    def delete():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delete, daemon=True).start()

# Hàm cập nhật tài khoản từ nội dung file txt
def update_accounts_from_text(service_key, text_content):
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    formatted_accounts = []
    for line in lines:
        # Hỗ trợ nhiều định dạng: email|pass, email pass, Email: ... | Pass: ...
        if '|' in line:
            parts = line.split('|', 1)
        elif ':' in line and '|' in line:
            parts = [line.split('|')[0].strip(), line.split('|')[1].strip()]
        else:
            parts = line.split(None, 1) if ' ' in line else [line]
        if len(parts) >= 2:
            email = parts[0].replace("Email:", "").strip()
            password = parts[1].replace("Pass:", "").strip()
            formatted = f"Email: {email} | Pass: {password}"
        else:
            formatted = line  # cho invite link canva
        formatted_accounts.append(formatted)
    FREE_ACCOUNTS[service_key]["accounts"] = formatted_accounts
    return len(formatted_accounts)

# Menu chọn dịch vụ để cập nhật
def admin_service_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, service in FREE_ACCOUNTS.items():
        kb.add(types.InlineKeyboardButton(
            text=f"{service['emoji']} {service['name']}",
            callback_data=f"update_{key}"
        ))
    return kb

# ================== XỬ LÝ FILE TXT TỪ ADMIN ==================

@bot.message_handler(content_types=['document'])
def handle_document(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    if not msg.document.file_name.lower().endswith('.txt'):
        bot.reply_to(msg, "❌ Chỉ chấp nhận file .txt thôi admin ơi!")
        return
    bot.reply_to(msg, "📄 Đã nhận file tài khoản!\n👇 Chọn dịch vụ muốn cập nhật:", reply_markup=admin_service_menu())
    admin_update_state[msg.from_user.id] = {"file_id": msg.document.file_id}

@bot.callback_query_handler(func=lambda call: call.data.startswith("update_"))
def handle_update_service(call):
    if call.from_user.id != ADMIN_ID:
        return
    service_key = call.data.split("_")[1]
    if call.from_user.id not in admin_update_state:
        bot.answer_callback_query(call.id, "❌ Không tìm thấy file!", show_alert=True)
        return
    file_id = admin_update_state[call.from_user.id]["file_id"]
    try:
        file_path = bot.get_file(file_id).file_path
        downloaded_file = bot.download_file(file_path)
        content = downloaded_file.decode('utf-8')
        count = update_accounts_from_text(service_key, content)
        bot.answer_callback_query(call.id, f"✅ Cập nhật thành công {count} tài khoản!", show_alert=True)
        bot.send_message(call.from_user.id,
                         f"🚀 Đã cập nhật <b>{count}</b> tài khoản cho <b>{FREE_ACCOUNTS[service_key]['name']}</b>\n"
                         f"Tồn kho hiện tại: {get_remaining_count(service_key)}", parse_mode="HTML")
        del admin_update_state[call.from_user.id]
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Lỗi khi xử lý file!", show_alert=True)
        bot.send_message(call.from_user.id, f"Lỗi: {str(e)}")

# ================== /start ==================

@bot.message_handler(commands=["start"])
def start(msg):
    welcome_text = (
        "🎉 <b>CHÀO MỪNG BẠN ĐẾN SHARE TÀI KHOẢN FREE</b>\n\n"
        "🔥 Chia sẻ tài khoản Pro/Teams miễn phí!\n\n"
        "⚠️ <i>Quy định:</i>\n"
        "• Mỗi ngày được lấy <b>tối đa 10 lần</b> cho mỗi dịch vụ\n"
        "• Mỗi lần nhận <b>1 tài khoản ngẫu nhiên</b>\n"
        "❤️ Dùng hợp lý, không đổi pass nhé!\n\n"
        f"{get_today_stats()}\n\n"
        "👇 Chọn dịch vụ còn hàng để nhận ngay!\n"
        "<i>Gõ capcut, chatgpt, canva, netflix, picsart, hma để mở nhanh</i>\n\n"
        "📹 <b>HƯỚNG DẪN SỬ DỤNG CHATGPT PLUS</b>\n"
        "Xem video hướng dẫn chi tiết cách dùng ChatGPT hiệu quả (dành cho người mới):\n"
        "https://youtu.be/u5GqqqJgfHQ\n"
        "https://yopmail.com/"
    )
    bot.send_message(msg.chat.id, welcome_text, parse_mode="HTML", reply_markup=inline_service_menu(), disable_web_page_preview=True)

# ================== /taikhoan ==================

@bot.message_handler(commands=["taikhoan"])
def taikhoan_command(msg):
    menu_text = (
        "📋 <b>Chọn dịch vụ để nhận 1 tài khoản free</b>\n"
        "(Mỗi ngày tối đa 10 lần mỗi dịch vụ)\n\n"
        f"{get_today_stats()}\n\n"
        "👇 Chọn bên dưới để nhận ngay!"
    )
    menu_msg = bot.send_message(msg.chat.id, menu_text, parse_mode="HTML", reply_markup=inline_service_menu())
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
    if selected_key:
        menu_text = (
            f"🔥 <b>Bạn muốn nhận {FREE_ACCOUNTS[selected_key]['name']}?</b>\n"
            f"(Mỗi ngày tối đa 10 lần)\n\n"
            f"{get_today_stats()}\n\n"
            "👇 Chọn bên dưới để nhận ngay!"
        )
        menu_msg = bot.send_message(msg.chat.id, menu_text, parse_mode="HTML", reply_markup=inline_service_menu())
        if msg.chat.type in ["group", "supergroup"]:
            delete_message_later(msg.chat.id, menu_msg.message_id, delay=15)

# ================== XỬ LÝ INLINE BUTTON ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("get_"))
def handle_inline_get(call):
    user_id = call.from_user.id
    service_key = call.data.split("_")[1]
    if service_key not in FREE_ACCOUNTS:
        try:
            bot.answer_callback_query(call.id, "❌ Dịch vụ không tồn tại!", show_alert=True)
        except:
            pass
        return
    service = FREE_ACCOUNTS[service_key]
    if len(service["accounts"]) == 0:
        try:
            bot.answer_callback_query(call.id, "🔴 Dịch vụ này đã hết tài khoản!", show_alert=True)
        except:
            pass
        return
    if not can_user_take_today(user_id, service_key):
        try:
            bot.answer_callback_query(call.id, f"⛔ Hôm nay bạn đã lấy đủ 10 lần {service['name']} rồi!\nNgày mai quay lại nhé ❤️", show_alert=True)
        except:
            pass
        return
    account = get_one_random_account(service_key)
    current_count = mark_user_taken(user_id, service_key)
    text = (
        f"{service['emoji']} <b>BẠN ĐÃ NHẬN THÀNH CÔNG!</b>\n\n"
        f"<b>Dịch vụ:</b> {service['name']}\n"
        f"<b>Tài khoản:</b>\n<code>{account}</code>\n\n"
        f"✅ Dùng hợp lý nhé!\n"
        f"📊 <b>Bạn đã lấy {current_count}/10 lần hôm nay</b>\n"
        f"🔄 Ngày mai reset lại 10 lần mới!"
    )
    if service_key == "chatgpt":
        text += (
            "\n\n📹 <b>HƯỚNG DẪN SỬ DỤNG</b>\n"
            "Xem video chi tiết cách dùng ChatGPT Plus hiệu quả (cập nhật 2025):\n"
            "https://youtu.be/u5GqqqJgfHQ\n"
            "https://yopmail.com/"
        )
    if service_key == "hma":
        text += (
            "\n\n🔐 <b>HƯỚNG DẪN SỬ DỤNG HMA VPN</b>\n"
            "1. Tải app HMA VPN tại: https://www.hidemyass.com/en-us/downloads\n"
            "2. Đăng nhập bằng Email + Pass\n"
            "3. Nếu yêu cầu License Key → Dán key vào phần Activate/Enter Key\n"
            "❤️ Không đổi pass để mọi người cùng dùng nhé!"
        )
    success = False
    try:
        bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=True)
        success = True
    except Exception:
        success = False
    try:
        if success:
            bot.answer_callback_query(call.id, f"✅ Đã gửi vào chat riêng (lần {current_count}/10)!", show_alert=False, cache_time=5)
        else:
            bot.answer_callback_query(call.id, "❌ Vui lòng /start bot ở chat riêng để nhận tài khoản!", show_alert=True, cache_time=5)
    except ApiTelegramException as e:
        if "query is too old" in str(e).lower() or "query ID is invalid" in str(e).lower():
            pass
        else:
            print(f"Lỗi answer_callback_query: {e}")

# ================== LỆNH ADMIN ==================

@bot.message_handler(commands=["reset", "resetall", "resetalltoday"])
def admin_commands(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "❌ Chỉ admin mới dùng lệnh này!")
        return
    # Giữ nguyên phần lệnh reset cũ của bạn (đã có trong code trước)

# ================== CHẠY BOT + FLASK ==================

if __name__ == "__main__":
    print("🤖 Bot Share Tài Khoản Free đang khởi động - Hỗ trợ cập nhật tài khoản bằng file .txt từ Admin...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"Lỗi bot: {e}")
        time.sleep(10)
