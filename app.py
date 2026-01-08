import telebot
from telebot import types
from pymongo import MongoClient
from datetime import datetime, date
import random
import threading
import time
import os
from flask import Flask, request, jsonify
from telebot.apihelper import ApiTelegramException

# ================== PAYOS (SỬA ĐÚNG 100% THEO SDK MỚI NHẤT - checkout_url) ==================
from payos import PayOS
from payos.types import CreatePaymentLinkRequest, ItemData  # Import đúng

# ================== CẤU HÌNH ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "free_share_bot")

PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
WEBHOOK_URL_BASE = os.getenv("WEBHOOK_URL_BASE")  # https://your-bot.onrender.com

if not all([BOT_TOKEN, MONGO_URI, PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY, WEBHOOK_URL_BASE]):
    raise ValueError("Thiếu biến môi trường quan trọng!")

payOS = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)

ADMIN_ID = 5589888565

# ================== TÀI KHOẢN FREE ==================
FREE_ACCOUNTS = {
    "capcut": {"name": "CapCut Pro", "emoji": "🎬", "keywords": ["capcut", "cap", "cut", "cap cut"], "accounts": []},
    "chatgpt": {"name": "ChatGPT Plus", "emoji": "🤖", "keywords": ["chatgpt", "gpt", "chat gpt", "ai"], "accounts": []},
    "canva": {"name": "Canva Pro Teams Free", "emoji": "🎨", "keywords": ["canva", "design", "thietke"], "accounts": []},
    "netflix": {"name": "Netflix Shared", "emoji": "📺", "keywords": ["netflix", "nf", "phim"], "accounts": []},
    "picsart": {"name": "Picsart Gold", "emoji": "🖼️", "keywords": ["picsart", "pic", "edit anh", "chinh anh"], "accounts": []},
    "hma": {"name": "HMA VPN Pro", "emoji": "🔒", "keywords": ["hma", "vpn", "hidemyass"], "accounts": []},
    "wink": {"name": "WINK VPN Pro", "emoji": "📸", "keywords": ["wink"], "accounts": []},
}

# ================== TÀI KHOẢN PREMIUM ==================
PAID_ACCOUNTS = {
    "chatgpt_premium": {
        "name": "ChatGPT Plus Riêng Tư (Premium)",
        "emoji": "🤖",
        "price": 150000,
        "keywords": ["chatgpt premium", "gpt premium", "chatgpt mua", "gpt mua"],
        "accounts": []
    },
    "netflix_premium": {
        "name": "Netflix 4K Private",
        "emoji": "📺",
        "price": 200000,
        "keywords": ["netflix premium", "nf premium", "netflix mua"],
        "accounts": []
    },
}

# ================== KHỞI TẠO ==================
bot = telebot.TeleBot(BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]
users_collection = db.users
orders_collection = db.orders

app = Flask(__name__)

admin_update_state = {}

# ================== HÀM HỖ TRỢ ==================
def get_remaining_count(accounts_list):
    count = len(accounts_list)
    if count == 0:
        return "🔴 Hết hàng"
    elif count <= 5:
        return f"🟡 Còn: {count} (Sắp hết)"
    else:
        return f"🟢 Còn: {count}"

def get_today_stats():
    today = date.today().isoformat()
    stats = []
    total_taken = 0
    for key, service in FREE_ACCOUNTS.items():
        taken = users_collection.count_documents({"service": key, "date": today})
        remaining = get_remaining_count(service["accounts"])
        stats.append(f"{service['emoji']} {service['name']}: {remaining} | <b>{taken} người lấy</b>")
        total_taken += taken
    for key, service in PAID_ACCOUNTS.items():
        sold = orders_collection.count_documents({"service_key": key, "date": today, "status": "success"})
        remaining = get_remaining_count(service["accounts"])
        stats.append(f"{service['emoji']} {service['name']}: {remaining} | <b>{sold} người mua</b>")
        total_taken += sold
    stats_text = "\n".join(stats)
    return f"📊 <b>THỐNG KÊ & TỒN KHO HÔM NAY</b>\n{stats_text}\n\n💥 <b>Tổng lượt lấy/mua: {total_taken}</b>"

def delete_message_later(chat_id, message_id, delay=15):
    def delete():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delete, daemon=True).start()

def can_user_take_today(user_id, service_key):
    today = date.today().isoformat()
    record = users_collection.find_one({"user_id": user_id, "service": service_key, "date": today})
    return not record or record.get("count", 0) < 10

def mark_user_taken(user_id, service_key):
    today = date.today().isoformat()
    result = users_collection.find_one_and_update(
        {"user_id": user_id, "service": service_key, "date": today},
        {"$inc": {"count": 1}, "$setOnInsert": {"taken_at": datetime.now()}},
        upsert=True,
        return_document=True
    )
    return result.get("count", 1)

def can_user_buy_today(user_id, service_key):
    today = date.today().isoformat()
    count = orders_collection.count_documents({
        "user_id": user_id,
        "service_key": service_key,
        "date": today,
        "status": "success"
    })
    return count == 0

def update_accounts_from_text(service_key, text_content, is_paid=False):
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    formatted = []
    for line in lines:
        if '|' in line:
            parts = line.split('|', 1)
        else:
            parts = line.split(None, 1) if ' ' in line else [line]
        if len(parts) >= 2:
            email = parts[0].replace("Email:", "").strip()
            password = parts[1].replace("Pass:", "").strip()
            formatted.append(f"Email: {email} | Pass: {password}")
        else:
            formatted.append(line)
    target = PAID_ACCOUNTS if is_paid else FREE_ACCOUNTS
    target[service_key]["accounts"] = formatted
    return len(formatted)

# ================== MENU ==================
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🆓 NHẬN TÀI KHOẢN FREE", callback_data="menu_free"))
    kb.add(types.InlineKeyboardButton("💎 MUA TÀI KHOẢN PREMIUM", callback_data="menu_paid"))
    return kb

def free_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, s in FREE_ACCOUNTS.items():
        rem = get_remaining_count(s["accounts"])
        if "Hết hàng" in rem: continue
        kb.add(types.InlineKeyboardButton(f"{s['emoji']} {s['name']} | {rem}", callback_data=f"get_{key}"))
    return kb

def paid_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, s in PAID_ACCOUNTS.items():
        if len(s["accounts"]) == 0: continue
        price = f"{s['price']:,}đ".replace(",", ".")
        kb.add(types.InlineKeyboardButton(f"{s['emoji']} {s['name']} | {price}", callback_data=f"buy_{key}"))
    return kb

def admin_type_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🆓 Free", callback_data="uptype_free"),
        types.InlineKeyboardButton("💎 Premium", callback_data="uptype_paid")
    )
    return kb

def admin_service_menu(is_paid=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    target = PAID_ACCOUNTS if is_paid else FREE_ACCOUNTS
    for key, s in target.items():
        kb.add(types.InlineKeyboardButton(f"{s['emoji']} {s['name']}", callback_data=f"upsvc_{key}_{'paid' if is_paid else 'free'}"))
    return kb

# ================== FLASK + WEBHOOK ==================
@app.route('/')
def health():
    return "Bot đang chạy khỏe mạnh! 🚀", 200

@app.route('/payos_webhook', methods=['POST'])
def payos_webhook():
    try:
        data = request.get_json(force=True)
        webhook_data = payOS.verifyPaymentWebhookData(data)
        if webhook_data.code == "00":
            order_code = webhook_data.orderCode
            order = orders_collection.find_one({"order_code": order_code, "status": "pending"})
            if order:
                user_id = order["user_id"]
                service_key = order["service_key"]
                if PAID_ACCOUNTS[service_key]["accounts"]:
                    account = random.choice(PAID_ACCOUNTS[service_key]["accounts"])
                    PAID_ACCOUNTS[service_key]["accounts"].remove(account)
                    text = (
                        f"🎉 <b>THANH TOÁN THÀNH CÔNG!</b>\n\n"
                        f"<b>Dịch vụ:</b> {PAID_ACCOUNTS[service_key]['name']}\n"
                        f"<b>Tài khoản riêng tư:</b>\n<code>{account}</code>\n\n"
                        f"❤️ Dùng thoải mái, không đổi pass nhé!\n"
                        f"📹 <b>HƯỚNG DẪN</b>: https://youtu.be/u5GqqqJgfHQ\n"
                        f"https://yopmail.com/"
                    )
                    bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=True)
                    orders_collection.update_one({"order_code": order_code}, {"$set": {"status": "success"}})
        return jsonify({"success": True})
    except Exception as e:
        print("Webhook error:", e)
        return jsonify({"error": str(e)}), 400

# ================== HANDLER ==================
@bot.message_handler(commands=["start"])
def start(msg):
    welcome = (
        "🎉 <b>CHÀO MỪNG BẠN ĐẾN BOT SHARE TÀI KHOẢN</b>\n\n"
        "🆓 Nhận tài khoản Pro miễn phí hàng ngày (tối đa 10 lần/dịch vụ)\n"
        "💎 Mua tài khoản riêng tư cao cấp qua PayOS (QR/VietQR)\n\n"
        f"{get_today_stats()}\n\n"
        "👇 Chọn bên dưới để bắt đầu!\n\n"
        "<i>Gõ tên dịch vụ như: capcut, chatgpt, netflix premium... để mở nhanh</i>"
    )
    bot.send_message(msg.chat.id, welcome, parse_mode="HTML", reply_markup=main_menu(), disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def keyword_handler(msg):
    text = msg.text.lower().strip()
    for key, s in FREE_ACCOUNTS.items():
        if any(kw in text for kw in s["keywords"]):
            menu_msg = bot.send_message(msg.chat.id, f"🔥 <b>{s['name']}</b>\n\n{get_today_stats()}", parse_mode="HTML", reply_markup=free_menu())
            if msg.chat.type in ["group", "supergroup"]:
                delete_message_later(msg.chat.id, menu_msg.message_id)
            return
    for key, s in PAID_ACCOUNTS.items():
        if any(kw in text for kw in s["keywords"]):
            menu_msg = bot.send_message(msg.chat.id, f"💎 <b>MUA {s['name']}</b>\n\n{get_today_stats()}", parse_mode="HTML", reply_markup=paid_menu())
            if msg.chat.type in ["group", "supergroup"]:
                delete_message_later(msg.chat.id, menu_msg.message_id)
            return

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "menu_free":
        bot.edit_message_text(f"🆓 <b>CHỌN DỊCH VỤ FREE</b>\n\n{get_today_stats()}", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=free_menu())
    elif call.data == "menu_paid":
        bot.edit_message_text(f"💎 <b>MUA TÀI KHOẢN PREMIUM</b>\n\n{get_today_stats()}", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=paid_menu())
    
    elif call.data.startswith("get_"):
        service_key = call.data.split("_")[1]
        service = FREE_ACCOUNTS[service_key]
        if not service["accounts"]:
            bot.answer_callback_query(call.id, "🔴 Hết tài khoản!", show_alert=True)
            return
        if not can_user_take_today(call.from_user.id, service_key):
            bot.answer_callback_query(call.id, "⛔ Hôm nay bạn đã lấy đủ 10 lần rồi! Ngày mai quay lại nhé ❤️", show_alert=True)
            return
        account = random.choice(service["accounts"])
        count = mark_user_taken(call.from_user.id, service_key)
        text = (
            f"{service['emoji']} <b>BẠN ĐÃ NHẬN THÀNH CÔNG!</b>\n\n"
            f"<b>Dịch vụ:</b> {service['name']}\n"
            f"<b>Tài khoản:</b>\n<code>{account}</code>\n\n"
            f"✅ Dùng hợp lý, không đổi pass nhé!\n"
            f"📊 <b>Bạn đã lấy {count}/10 lần hôm nay</b>"
        )
        if service_key == "chatgpt":
            text += (
                "\n\n📹 <b>HƯỚNG DẪN SỬ DỤNG CHATGPT PLUS</b>\n"
                "Xem video chi tiết:\n"
                "https://youtu.be/u5GqqqJgfHQ\n"
                "https://yopmail.com/"
            )
        try:
            bot.send_message(call.from_user.id, text, parse_mode="HTML", disable_web_page_preview=True)
            bot.answer_callback_query(call.id, f"✅ Đã gửi vào tin nhắn riêng (lần {count}/10)!")
        except:
            bot.answer_callback_query(call.id, "❌ Vui lòng /start bot ở chat riêng để nhận!", show_alert=True)
    
    elif call.data.startswith("buy_"):
        service_key = call.data.split("_")[1]
        service = PAID_ACCOUNTS[service_key]
        user_id = call.from_user.id
        if not service["accounts"]:
            bot.answer_callback_query(call.id, "🔴 Hết tài khoản premium!", show_alert=True)
            return
        if not can_user_buy_today(user_id, service_key):
            bot.answer_callback_query(call.id, "⛔ Hôm nay bạn đã mua dịch vụ này rồi!", show_alert=True)
            return
        
        order_code = int(time.time() * 1000)
        items = [ItemData(name=service["name"], quantity=1, price=service["price"])]
        
        payment_data = CreatePaymentLinkRequest(
            orderCode=order_code,
            amount=service["price"],
            description=f"Mua {service['name']} - User {user_id}",
            items=items,
            returnUrl=WEBHOOK_URL_BASE,
            cancelUrl=WEBHOOK_URL_BASE
        )
        
        try:
            result = payOS.payment_requests.create(payment_data=payment_data)
            checkout_url = result.checkout_url  # <--- SỬA CHÍNH Ở ĐÂY: checkout_url (chữ u thường)
            
            orders_collection.insert_one({
                "order_code": order_code,
                "user_id": user_id,
                "service_key": service_key,
                "status": "pending",
                "date": date.today().isoformat(),
                "created_at": datetime.now()
            })
            
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("💳 Thanh toán ngay (PayOS QR)", url=checkout_url))
            
            bot.send_message(user_id,
                             f"💎 <b>MUA {service['name']}</b>\n\n"
                             f"Giá: <b>{service['price']:,}đ</b>\n\n"
                             f"Thanh toán xong → tài khoản riêng tư gửi tự động!\n"
                             f"⏰ Link hết hạn sau 15 phút.",
                             parse_mode="HTML", reply_markup=kb)
            bot.answer_callback_query(call.id, "🔗 Link thanh toán đã gửi vào chat riêng!")
        except Exception as e:
            bot.answer_callback_query(call.id, "❌ Lỗi tạo link thanh toán!", show_alert=True)
            print("PayOS error:", e)

# ================== ADMIN UP FILE ==================
@bot.message_handler(content_types=['document'])
def handle_document(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    if not msg.document.file_name.lower().endswith('.txt'):
        bot.reply_to(msg, "❌ Chỉ chấp nhận file .txt thôi admin!")
        return
    bot.reply_to(msg, "📄 Đã nhận file!\n👉 Chọn loại tài khoản muốn cập nhật:", reply_markup=admin_type_menu())
    admin_update_state[msg.from_user.id] = {"file_id": msg.document.file_id}

@bot.callback_query_handler(func=lambda call: call.data.startswith("uptype_"))
def choose_type(call):
    if call.from_user.id != ADMIN_ID:
        return
    up_type = call.data.split("_")[1]
    is_paid = (up_type == "paid")
    bot.edit_message_text("👉 Chọn dịch vụ muốn cập nhật:", call.message.chat.id, call.message.message_id, reply_markup=admin_service_menu(is_paid))
    admin_update_state[call.from_user.id]["type"] = up_type

@bot.callback_query_handler(func=lambda call: call.data.startswith("upsvc_"))
def update_service(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split("_")
    service_key = parts[1]
    up_type = parts[2]
    is_paid = (up_type == "paid")
    
    state = admin_update_state.get(call.from_user.id)
    if not state or "file_id" not in state:
        bot.answer_callback_query(call.id, "❌ Không tìm thấy file!", show_alert=True)
        return
    
    file_id = state["file_id"]
    try:
        file_path = bot.get_file(file_id).file_path
        downloaded = bot.download_file(file_path)
        content = downloaded.decode('utf-8')
        count = update_accounts_from_text(service_key, content, is_paid)
        target_name = PAID_ACCOUNTS[service_key]["name"] if is_paid else FREE_ACCOUNTS[service_key]["name"]
        remaining = get_remaining_count(PAID_ACCOUNTS[service_key]["accounts"] if is_paid else FREE_ACCOUNTS[service_key]["accounts"])
        
        bot.answer_callback_query(call.id, f"✅ Đã cập nhật {count} tài khoản!", show_alert=True)
        bot.send_message(call.from_user.id,
                         f"🚀 Đã cập nhật <b>{count}</b> tài khoản cho <b>{target_name}</b>\n"
                         f"Tồn kho hiện tại: {remaining}", parse_mode="HTML")
        del admin_update_state[call.from_user.id]
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Lỗi xử lý file!", show_alert=True)
        bot.send_message(call.from_user.id, f"Lỗi: {str(e)}")

# ================== CHẠY BOT + FLASK ==================
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("🤖 Bot Share Free + Premium (PayOS SDK hoàn chỉnh - checkout_url đã sửa) đang khởi động...")
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling(none_stop=True)
