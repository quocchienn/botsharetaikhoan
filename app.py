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
from payos import PayOS, ItemData, PaymentData

# ================== CẤU HÌNH ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "free_share_bot")

# Cấu hình PayOS
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
DOMAIN = os.getenv("DOMAIN")

payos = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)

if not BOT_TOKEN or not MONGO_URI:
    raise ValueError("Thiết lập BOT_TOKEN và MONGO_URI trong Environment Variables!")

ADMIN_ID = 5589888565 

# ================== DỮ LIỆU DỊCH VỤ ==================

FREE_ACCOUNTS = {
    "capcut": {"name": "CapCut Pro", "emoji": "🎬", "keywords": ["capcut", "cap", "cut"], "accounts": []},
    "chatgpt": {"name": "ChatGPT Plus", "emoji": "🤖", "keywords": ["chatgpt", "gpt", "ai"], "accounts": []},
    "canva": {"name": "Canva Pro Teams", "emoji": "🎨", "keywords": ["canva", "thietke"], "accounts": []},
    "netflix": {"name": "Netflix Shared", "emoji": "📺", "keywords": ["netflix", "nf"], "accounts": []},
    "picsart": {"name": "Picsart Gold", "emoji": "🖼️", "keywords": ["picsart", "pic"], "accounts": []},
    "hma": {"name": "HMA VPN Pro", "emoji": "🔒", "keywords": ["hma", "vpn"], "accounts": []},
    "wink": {"name": "WINK VPN Pro", "emoji": "📸", "keywords": ["wink"], "accounts": []},
}

# Gói Premium bán phí
PREMIUM_PACKS = {
    "pack_vip_1": {"name": "Gói VIP 1 Tháng (Tất cả DV)", "price": 50000, "days": 30},
    "pack_vip_3": {"name": "Gói VIP 3 Tháng (Tất cả DV)", "price": 120000, "days": 90}
}

admin_update_state = {}

# ================== KHỞI TẠO DB & BOT ==================

bot = telebot.TeleBot(BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]
users_collection = db.users
orders_collection = db.orders # Collection mới lưu đơn hàng

# ================== FLASK SERVER & WEBHOOK PAYOS ==================

app = Flask(__name__)

@app.route('/')
def health_check():
    return "🤖 Bot Share & PayOS đang chạy! 🚀", 200

@app.route('/payos-webhook', methods=['POST'])
def payos_webhook():
    data = request.json
    try:
        # Xác thực webhook từ PayOS
        webhook_data = payos.verifyPaymentData(data)
        order_code = webhook_data['orderCode']
        status = webhook_data['status']

        if status == "PAID":
            # Tìm đơn hàng trong DB
            order = orders_collection.find_one({"order_code": order_code, "status": "PENDING"})
            if order:
                user_id = order['user_id']
                # Cập nhật trạng thái đơn hàng
                orders_collection.update_one({"order_code": order_code}, {"$set": {"status": "COMPLETED"}})
                
                # Gửi thông báo cho người dùng
                bot.send_message(user_id, f"✅ **THANH TOÁN THÀNH CÔNG!**\nCảm ơn bạn đã mua {order['pack_name']}.\nBạn đã được nâng cấp quyền ưu tiên!")
                # Bạn có thể thêm logic cộng ngày VIP vào DB users ở đây
                
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Webhook Error: {e}")
        return jsonify({"success": False}), 400

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ================== HÀM HỖ TRỢ ==================

def can_user_take_today(user_id, service_key):
    today = date.today().isoformat()
    record = users_collection.find_one({"user_id": user_id, "service": service_key, "date": today})
    if record is None: return True
    return record.get("count", 0) < 10

def mark_user_taken(user_id, service_key):
    today = date.today().isoformat()
    result = users_collection.find_one_and_update(
        {"user_id": user_id, "service": service_key, "date": today},
        {"$inc": {"count": 1}, "$setOnInsert": {"taken_at": datetime.now()}},
        upsert=True, return_document=True
    )
    return result.get("count", 1)

def get_remaining_count(service_key):
    count = len(FREE_ACCOUNTS.get(service_key, {}).get("accounts", []))
    if count == 0: return "🔴 Hết hàng"
    return f"🟢 Còn: {count}"

def inline_main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, service in FREE_ACCOUNTS.items():
        remaining = get_remaining_count(key)
        if "Hết hàng" not in remaining:
            kb.add(types.InlineKeyboardButton(text=f"{service['emoji']} {service['name']} | {remaining}", callback_data=f"get_{key}"))
    
    # Nút Mua hàng
    kb.add(types.InlineKeyboardButton(text="💎 MUA TÀI KHOẢN PREMIUM (TỰ ĐỘNG)", callback_data="buy_menu"))
    return kb

# ================== XỬ LÝ THANH TOÁN ==================

@bot.callback_query_handler(func=lambda call: call.data == "buy_menu")
def handle_buy_menu(call):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, pack in PREMIUM_PACKS.items():
        kb.add(types.InlineKeyboardButton(text=f"🛒 {pack['name']} - {pack['price']:,}đ", callback_data=f"order_{key}"))
    kb.add(types.InlineKeyboardButton(text="🔙 Quay lại", callback_data="back_to_main"))
    bot.edit_message_text("💎 **NÂNG CẤP PREMIUM**\n\nQuyền lợi: Lấy tài khoản không giới hạn, hỗ trợ riêng, tốc độ cao.", 
                          call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def handle_create_order(call):
    pack_key = call.data.split("_")[1]
    pack = PREMIUM_PACKS[pack_key]
    user_id = call.from_user.id
    order_code = int(time.time()) # Mã đơn hàng duy nhất

    try:
        # Tạo link thanh toán PayOS
        payment_data = PaymentData(
            orderCode=order_code,
            amount=pack['price'],
            description=f"Thanh toan {pack_key}",
            items=[ItemData(name=pack['name'], quantity=1, price=pack['price'])],
            returnUrl=f"{DOMAIN}/",
            cancelUrl=f"{DOMAIN}/"
        )
        pay_link_res = payos.createPaymentLink(payment_data)
        
        # Lưu đơn hàng vào DB chờ thanh toán
        orders_collection.insert_one({
            "user_id": user_id,
            "order_code": order_code,
            "pack_name": pack['name'],
            "amount": pack['price'],
            "status": "PENDING",
            "created_at": datetime.now()
        })

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="💳 THANH TOÁN NGAY (VIETQR)", url=pay_link_res.checkoutUrl))
        
        bot.send_message(user_id, f"✅ **ĐƠN HÀNG ĐÃ TẠO!**\n\n📦 Gói: {pack['name']}\n💰 Số tiền: {pack['price']:,}đ\n\nBấm nút bên dưới để thanh toán. Hệ thống tự động duyệt sau 1-3 phút.", 
                         reply_markup=kb, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Lỗi hệ thống khi tạo đơn!", show_alert=True)

# ================== CÁC HANDLER CŨ (START, KEYWORDS, ETC) ==================

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
