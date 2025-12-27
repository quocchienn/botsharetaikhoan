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
            "Email: hocey76005@m3player.com | Pass: Chien2007",
            "Email: xadas61730@m3player.com | Pass: Chien2k5",
            "Email: fajic10847@m3player.com | Pass: Freecamdoihoi",
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
        "<i>Gõ capcut, chatgpt, canva, netflix, picsart để mở nhanh</i>\n\n"
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
    
    # Tin nhắn cơ bản (không thêm video cho Picsart)
    text = (
        f"{service['emoji']} <b>BẠN ĐÃ NHẬN THÀNH CÔNG!</b>\n\n"
        f"<b>Dịch vụ:</b> {service['name']}\n"
        f"<b>Tài khoản:</b>\n<code>{account}</code>\n\n"
        f"✅ Dùng hợp lý nhé!\n"
        f"📊 <b>Bạn đã lấy {current_count}/10 lần hôm nay</b>\n"
        f"🔄 Ngày mai reset lại 10 lần mới!"
    )
    
    # Chỉ thêm video hướng dẫn cho ChatGPT
    if service_key == "chatgpt":
        text += (
"\n\n📹 <b>HƯỚNG DẪN SỬ DỤNG</b>\n"
        "Xem video chi tiết cách dùng ChatGPT Plus hiệu quả (cập nhật 2025):\n"
        "https://youtu.be/u5GqqqJgfHQ\n"
        "https://yopmail.com/"
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
            bot.reply_to(msg, "❌ Dịch vụ không tồn tại! Có: capcut, chatgpt, canva, netflix, picsart")
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
            bot.reply_to(msg, "❌ Dịch vụ không tồn tại! Có: capcut, chatgpt, canva, netflix, picsart")
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
