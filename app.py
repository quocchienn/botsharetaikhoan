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

# ================== DANH SÁCH TÀI KHOẢN FREE ==================

FREE_ACCOUNTS = {
    "capcut": {
        "name": "CapCut Pro",
        "emoji": "🎬",
        "keywords": ["capcut", "cap", "cut", "cap cut"],
        "accounts": [
            "Email: travon75mjma63kc@hunght1890.com | Pass: a123456",
"Email: edgardo_botsmjma6q6b@hunght1890.com | Pass: a123456",
"Email: justina.romamjma64gc@hunght1890.com | Pass: a123456",
"Email: antwon67mjma654c@hunght1890.com | Pass: a123456",
"Email: adam.bayermjma6p3l@hunght1890.com | Pass: a123456",
"Email: tiffany.blocmjma65f9@hunght1890.com | Pass: a123456",
"Email: santos_keelimjma6q11@hunght1890.com | Pass: a123456",
"Email: danyka72mjma64ky@hunght1890.com | Pass: a123456",
"Email: clifton25mjma644e@hunght1890.com | Pass: a123456",
"Email: gia_williamsmjma6q38@hunght1890.com | Pass: a123456",
"Email: edgardo.bayemjma64tu@hunght1890.com | Pass: a123456",
"Email: demarco_corkmjma646m@hunght1890.com | Pass: a123456",
"Email: donavon24mjma63yt@hunght1890.com | Pass: a123456",
"Email: taylor.shanamjma6pa1@hunght1890.com | Pass: a123456",
"Email: clark63mjma6ozh@hunght1890.com | Pass: a123456",
"Email: ramiro_moscimjma63py@hunght1890.com | Pass: a123456",
"Email: brice.kreigemjma63yd@hunght1890.com | Pass: a123456",
"Email: malinda.krajmjma64d9@hunght1890.com | Pass: a123456",
"Email: arnoldo_kulamjma63w6@hunght1890.com | Pass: a123456",
"Email: nolan71mjma647x@hunght1890.com | Pass: a123456",
"Email: jaylen_harvemjma63kc@hunght1890.com | Pass: a123456",
"Email: violet_zulaumjn5x15p@hunght1890.com | Pass: a123456",
"Email: taya.conn9mjn5uzun@hunght1890.com | Pass: a123456",
"Email: kristin84mjn5x0go@hunght1890.com | Pass: a123456",
"Email: nyasia_bartemjn5x1qa@hunght1890.com | Pass: a123456",
"Email: icie.beahangmjn5x0x2@hunght1890.com | Pass: a123456",
"Email: lorena_nitzsmjn5x1uz@hunght1890.com | Pass: a123456",
"Email: llewellyn_bamjn5x0d7@hunght1890.com | Pass: a123456",
"Email: nicklaus_termjn5uyv8@hunght1890.com | Pass: a123456",
"Email: macy8mjn5x12p@hunght1890.com | Pass: a123456",
"Email: ova_blickmjn5x1sf@hunght1890.com | Pass: a123456",
"Email: austen_bogismjn5x1p1@hunght1890.com | Pass: a123456",
"Email: skylar_dickemjn5x0w8@hunght1890.com | Pass: a123456",
"Email: vernice.hodkmjn5x129@hunght1890.com | Pass: a123456",
"Email: willow31mjn5x10y@hunght1890.com | Pass: a123456",
"Email: candido.stramjn5uzok@hunght1890.com | Pass: a123456",
"Email: amy_crooks94mjn5x0e2@hunght1890.com | Pass: a123456",
"Email: gunnar_greenmjn5x0pq@hunght1890.com | Pass: a123456",
"Email: victoria_swamjn5x0hy@hunght1890.com | Pass: a123456",
"Email: corene79mjn5x00y@hunght1890.com | Pass: a123456",
"Email: freeman_kuphmjn5v0c2@hunght1890.com | Pass: a123456",
"Email: lavinia6mjn5x1es@hunght1890.com | Pass: a123456",
"Email: walker89mjn5x0t4@hunght1890.com | Pass: a123456",
"Email: trevor_boscomjn5x0md@hunght1890.com | Pass: a123456",
"Email: shyann.mertzmjn5xyxn@hunght1890.com | Pass: a123456",
"Email: peyton_hegmamjn5xyim@hunght1890.com | Pass: a123456",
"Email: harvey82mjn5uee7@hunght1890.com | Pass: a123456",
"Email: dameon.abernmjn5tb21@hunght1890.com | Pass: a123456",
"Email: gerson.kirlimjn5tc4z@hunght1890.com | Pass: a123456",
"Email: opal_toy82mjn5ued3@hunght1890.com | Pass: a123456",
"Email: jeremie.oharmjn5tc08@hunght1890.com | Pass: a123456",
"Email: lola53mjn5ucjh@hunght1890.com | Pass: a123456",
"Email: markus70mjn5ucqc@hunght1890.com | Pass: a123456",
"Email: ruby.shieldsmjn5uckr@hunght1890.com | Pass: a123456",
"Email: nakia83mjn5udwh@hunght1890.com | Pass: a123456",
"Email: aidan_kilbacmjn5tc4z@hunght1890.com | Pass: a123456",
"Email: leslie_wehnemjn5udxr@hunght1890.com | Pass: a123456",
"Email: reanna50mjn5ucz2@hunght1890.com | Pass: a123456",
"Email: rachael_treumjn5tc8w@hunght1890.com | Pass: a123456",
"Email: barney_bernimjn5ucsw@hunght1890.com | Pass: a123456",
"Email: elda_buckridmjn5uepn@hunght1890.com | Pass: a123456",
"Email: alphonso18mjn5tcx9@hunght1890.com | Pass: a123456",
"Email: velma_mante5mjn5udmj@hunght1890.com | Pass: a123456",
"Email: delores.wardmjn5uckb@hunght1890.com | Pass: a123456",
"Email: jacky.labadimjn5udt1@hunght1890.com | Pass: a123456",
"Email: claudie1mjn5tcjc@hunght1890.com | Pass: a123456",
"Email: jacquelyn_romjn5tcom@hunght1890.com | Pass: a123456",
"Email: osborne.greemjn5udbc@hunght1890.com | Pass: a123456",
"Email: leonard.kunzmjn5ue3e@hunght1890.com | Pass: a123456",
"Email: sean_crooks8mjn5udl9@hunght1890.com | Pass: a123456",
"Email: nelda.marquamjn5tbtq@hunght1890.com | Pass: a123456",
"Email: mafalda_blanmjn5tb51@hunght1890.com | Pass: a123456",
"Email: montana47mjn5ued3@hunght1890.com | Pass: a123456",
"Email: eleanora16mjn5udnu@hunght1890.com | Pass: a123456"
        ]
    },
    "chatgpt": {
        "name": "ChatGPT Plus",
        "emoji": "🤖",
        "keywords": ["chatgpt", "gpt", "chat gpt", "ai"],
        "accounts": [
            "Email: fraunnapreneiquau-6959@tmp.x-lab.net | Pass: quocchien273612",
            "Email: yupouseummoufei-5332@afw.fr.nf | Pass: quocchien1231451",
            "Email: vageissuzittau-5813@afw.fr.nf | Pass: quocchien7134156",
            "Email: ditufrimallei-6298@afw.fr.nf | Pass: quocchien1231616",
            "Email: jitonnbufa-8521@sindwir.com | Pass: quocchien089562",
        ]
    },
    "canva": {
        "name": "Canva Pro Teams Free",
        "emoji": "🎨",
        "keywords": ["canva", "design", "thietke", "can va"],
        "accounts": [
            "Invite link: https://www.canva.com/brand/join?token=xtJSXSD3-EgYjrGntr1jxA&referrer=team-invite",
        ]
    },
    "netflix": {
        "name": "Netflix Shared",
        "emoji": "📺",
        "keywords": ["netflix", "nf", "phim", "net flix"],
        "accounts": []  # ← Để trống như này = hết hàng
    },
    "picsart": {
        "name": "Picsart Gold",
        "emoji": "🖼️",
        "keywords": ["picsart", "pic", "pics art", "edit anh", "chinh anh"],
        "accounts": [
            "Email: sifafoilosi-2195@bboys.fr.nf | Pass: Chien2058375",
        ]
    },
    "hma": {
        "name": "HMA VPN Pro",
        "emoji": "🔒",
        "keywords": ["hma", "vpn", "hide my ass", "hidemyass", "proxy"],
        "accounts": [
            "Email: hackiosipa@gmail.com | Pass: Chien2k5 | License Key: MTBUYN-4RCRWJ-5RUHF2",
            # Bạn có thể thêm nhiều hơn nếu có
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
    return record.get("count", 0) < 10  # Giới hạn 10 lần/ngày

def mark_user_taken(user_id, service_key):
    today = date.today().isoformat()
    result = users_collection.find_one_and_update(
        {"user_id": user_id,
         "service": service_key,
         "date": today},
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
        taken = users_collection.count_documents({
            "service": key,
            "date": today
        })
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
    
    bot.send_message(
        msg.chat.id,
        welcome_text,
        parse_mode="HTML",
        reply_markup=inline_service_menu(),
        disable_web_page_preview=True
    )

# ================== /taikhoan ==================

@bot.message_handler(commands=["taikhoan"])
def taikhoan_command(msg):
    menu_text = (
        "📋 <b>Chọn dịch vụ để nhận 1 tài khoản free</b>\n"
        "(Mỗi ngày tối đa 10 lần mỗi dịch vụ)\n\n"
        f"{get_today_stats()}\n\n"
        "👇 Chọn bên dưới để nhận ngay!"
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
    
    if selected_key:
        menu_text = (
            f"🔥 <b>Bạn muốn nhận {FREE_ACCOUNTS[selected_key]['name']}?</b>\n"
            f"(Mỗi ngày tối đa 10 lần)\n\n"
            f"{get_today_stats()}\n\n"
            "👇 Chọn bên dưới để nhận ngay!"
        )
        
        menu_msg = bot.send_message(
            msg.chat.id,
            menu_text,
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
        try:
            bot.answer_callback_query(call.id, "❌ Dịch vụ không tồn tại!", show_alert=True)
        except (ApiTelegramException, Exception):
            pass
        return
    
    service = FREE_ACCOUNTS[service_key]
    
    if len(service["accounts"]) == 0:
        try:
            bot.answer_callback_query(call.id, "🔴 Dịch vụ này đã hết tài khoản!", show_alert=True)
        except (ApiTelegramException, Exception):
            pass
        return
    
    if not can_user_take_today(user_id, service_key):
        try:
            bot.answer_callback_query(
                call.id,
                f"⛔ Hôm nay bạn đã lấy đủ 10 lần {service['name']} rồi!\nNgày mai quay lại nhé ❤️",
                show_alert=True
            )
        except (ApiTelegramException, Exception):
            pass
        return
    
    account = get_one_random_account(service_key)
    current_count = mark_user_taken(user_id, service_key)
    
    # Tin nhắn cơ bản
    text = (
        f"{service['emoji']} <b>BẠN ĐÃ NHẬN THÀNH CÔNG!</b>\n\n"
        f"<b>Dịch vụ:</b> {service['name']}\n"
        f"<b>Tài khoản:</b>\n<code>{account}</code>\n\n"
        f"✅ Dùng hợp lý nhé!\n"
        f"📊 <b>Bạn đã lấy {current_count}/10 lần hôm nay</b>\n"
        f"🔄 Ngày mai reset lại 10 lần mới!"
    )
    
    # Chỉ thêm hướng dẫn cho ChatGPT
    if service_key == "chatgpt":
        text += (
            "\n\n📹 <b>HƯỚNG DẪN SỬ DỤNG</b>\n"
            "Xem video chi tiết cách dùng ChatGPT Plus hiệu quả (cập nhật 2025):\n"
            "https://youtu.be/u5GqqqJgfHQ\n"
            "https://yopmail.com/"
        )
    
    # Hướng dẫn riêng cho HMA VPN
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
            bot.answer_callback_query(
                call.id, 
                f"✅ Đã gửi vào chat riêng (lần {current_count}/10)!",
                show_alert=False,
                cache_time=5
            )
        else:
            bot.answer_callback_query(
                call.id, 
                "❌ Vui lòng /start bot ở chat riêng để nhận tài khoản!",
                show_alert=True,
                cache_time=5
            )
    except ApiTelegramException as e:
        if "query is too old" in str(e).lower() or "query ID is invalid" in str(e).lower():
            pass
        else:
            print(f"Lỗi answer_callback_query khác: {e}")
    except Exception as e:
        print(f"Lỗi không mong muốn khi answer callback: {e}")

# ================== LỆNH ADMIN ==================

@bot.message_handler(commands=["reset"])
def reset_user(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "❌ Chỉ admin mới dùng lệnh này!")
        return
    
    try:
        parts = msg.text.split()
        if len(parts) != 3:
            bot.reply_to(msg, "Sử dụng: /reset <dịch_vụ> <user_id>\nVí dụ: /reset capcut 123456789")
            return
        
        service_key = parts[1].lower()
        user_id = int(parts[2])
        
        if service_key not in FREE_ACCOUNTS:
            bot.reply_to(msg, "❌ Dịch vụ không tồn tại! Có: capcut, chatgpt, canva, netflix, picsart, hma")
            return
        
        today = date.today().isoformat()
        result = users_collection.delete_one({
            "user_id": user_id,
            "service": service_key,
            "date": today
        })
        
        if result.deleted_count > 0:
            bot.reply_to(msg, f"✅ Đã reset lượt lấy {FREE_ACCOUNTS[service_key]['name']} hôm nay cho user {user_id}")
        else:
            bot.reply_to(msg, f"ℹ️ User {user_id} chưa lấy {FREE_ACCOUNTS[service_key]['name']} hôm nay")
    
    except ValueError:
        bot.reply_to(msg, "❌ User ID phải là số!")
    except Exception as e:
        bot.reply_to(msg, f"❌ Lỗi: {e}")

@bot.message_handler(commands=["resetall"])
def reset_all_service(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "❌ Chỉ admin mới dùng lệnh này!")
        return
    
    try:
        parts = msg.text.split()
        if len(parts) != 2:
            bot.reply_to(msg, "Sử dụng: /resetall <dịch_vụ>\nVí dụ: /resetall capcut")
            return
        
        service_key = parts[1].lower()
        
        if service_key not in FREE_ACCOUNTS:
            bot.reply_to(msg, "❌ Dịch vụ không tồn tại! Có: capcut, chatgpt, canva, netflix, picsart, hma")
            return
        
        today = date.today().isoformat()
        result = users_collection.delete_many({
            "service": service_key,
            "date": today
        })
        
        bot.reply_to(msg, f"✅ Đã reset {FREE_ACCOUNTS[service_key]['name']} cho <b>{result.deleted_count}</b> người dùng hôm nay!", parse_mode="HTML")
    
    except Exception as e:
        bot.reply_to(msg, f"❌ Lỗi: {e}")

@bot.message_handler(commands=["resetalltoday"])
def reset_all_today(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "❌ Chỉ admin mới dùng lệnh này!")
        return
    
    try:
        today = date.today().isoformat()
        result = users_collection.delete_many({"date": today})
        
        bot.reply_to(msg, f"🔥 Đã reset hoàn toàn lượt lấy hôm nay!\nXóa <b>{result.deleted_count}</b> bản ghi của tất cả dịch vụ.", parse_mode="HTML")
    
    except Exception as e:
        bot.reply_to(msg, f"❌ Lỗi: {e}")

# ================== CHẠY BOT + FLASK ==================

if __name__ == "__main__":
    print("🤖 Bot Share Tài Khoản Free đang khởi động với tồn kho và thống kê...")
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"Lỗi bot: {e}")
        time.sleep(10)
