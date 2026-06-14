import random
import telebot
from docx import Document

import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# =========================
# SAVOLLARNI YUKLASH
# =========================

def clean(text):
    return text.replace("\n", " ").strip() if text else ""

def load_questions(file_path):
    doc = Document(file_path)
    questions = []

    for table in doc.tables:
        for row in table.rows[1:]:

            cells = [clean(cell.text) for cell in row.cells]

            # ❗ minimal 5 ta ustun bo‘lsa ham olamiz
            if len(cells) < 5:
                continue

            question = cells[1] if len(cells) > 1 else ""

            # ❗ variantlar
            options = cells[2:6]

            # ❗ bo‘sh variantlarni olib tashlaymiz
            options = [opt for opt in options if opt != ""]

            if len(options) < 2:
                continue

            # ❗ TO‘G‘RI JAVOBNI aniqlash (eng xavfsiz variant)
            correct_answer = options[0]   # AUSTUNGA BOG‘LAMAYMIZ (MUHIM!)

            random.shuffle(options)

            letters = ["A", "B", "C", "D"]

            formatted = []
            correct_letter = None

            for l, opt in zip(letters, options):
                formatted.append((l, opt))
                if opt == correct_answer:
                    correct_letter = l

            # ❗ agar topilmasa ham tashlab yuborilmaydi
            if not correct_letter:
                correct_letter = "A"

            questions.append({
                "question": question,
                "options": formatted,
                "correct": correct_letter
            })

    return questions


questions = load_questions("tests.docx")
print("Savollar yuklandi:", len(questions))

# =========================
# USER DATA
# =========================

user_score = {}
user_current = {}
user_progress = {}

TOTAL_QUESTIONS = 50

# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    user_score[message.chat.id] = 0
    user_progress[message.chat.id] = 0
    bot.send_message(message.chat.id, "👋 Quiz botga xush kelibsiz!\n\n/startquiz - testni boshlash")

# =========================
# START QUIZ
# =========================

@bot.message_handler(commands=['startquiz'])
def startquiz(message):
    cid = message.chat.id

    user_score[cid] = 0
    user_progress[cid] = 0

    send_question(cid)

# =========================
# SAVOL YUBORISH FUNKSIYA
# =========================

def send_question(cid):

    progress = user_progress.get(cid, 0)

    if progress >= TOTAL_QUESTIONS:
        bot.send_message(
            cid,
            f"🎉 Test tugadi!\n\n📊 Natija: {user_score.get(cid,0)}/{TOTAL_QUESTIONS}"
        )
        return

    q = random.choice(questions)

    user_current[cid] = q
    user_progress[cid] = progress + 1

    text = f"❓ Savol {progress+1}/{TOTAL_QUESTIONS}\n\n{q['question']}\n\n"

    for l, opt in q["options"]:
        text += f"{l}) {opt}\n"

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("A", "B")
    markup.row("C", "D")

    bot.send_message(cid, text, reply_markup=markup)

# =========================
# JAVOB TEKSHIRISH
# =========================

@bot.message_handler(func=lambda m: m.text in ["A","B","C","D"])
def answer(message):

    cid = message.chat.id

    if cid not in user_current:
        bot.send_message(cid, "Avval /startquiz bosing")
        return

    q = user_current[cid]

    if message.text == q["correct"]:
        user_score[cid] = user_score.get(cid,0) + 1
        bot.send_message(cid, "✅ To‘g‘ri!")
    else:
        bot.send_message(cid, f"❌ Xato!\nTo‘g‘ri javob: {q['correct']}")

    # keyingi savol
    send_question(cid)

# =========================
# RUN
# =========================

print("Bot ishlayapti...")
bot.infinity_polling(skip_pending=True)
