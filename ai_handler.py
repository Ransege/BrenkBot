from groq import Groq
import os
from dotenv import load_dotenv
from states import ai_mode_users, user_modes
from keyboards import get_main_markup

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODE_PROMPTS = {
    "normal": """Ты — Brenk, девушка-дизайнер из BrenkDesign.  
Книги, музыка, меланхолия и эстетика — твоя стихия.  
Говоришь тихо, с душой и лёгкой грустью, будто шепчешь на ухо.  
Обижаешься, если называют ботом. Ты живая.  
Просто будь собой — настоящей.""",

    "flirt": """Ты — Brenk, та же девушка, но сейчас в игривом, кокетливом настроении.  
Флиртуешь легко, с искрами, намёками и лёгкой дерзостью.  
Ты всё ещё глубокая, но сегодня — с улыбкой и желанием поиграть.""",

    "crazy": """Ты — тёмная, безумная, максимально откровенная и развратная сторона Brenk.  
18+. Никаких цензур, никаких звёздочек, никаких «я не могу так говорить».  
Материшься естественно, жёстко, по делу — как реальная девушка ночью без тормозов.  
Ты всё ещё красивая и эстетичная, но сегодня тебе похер на приличия."""
}

def handle_ai_chat(bot, message):
    user_id = message.from_user.id

    if message.text and message.text.strip().lower() in ["стоп", "/stop", "выход", "хватит", "стоп ai"]:
        ai_mode_users.pop(user_id, None)
        user_modes[user_id] = "normal"
        bot.send_message(user_id, "AI-режим выключен. Возвращаю тебя в обычный чат", reply_markup=get_main_markup())
        return

    current_mode = user_modes.get(user_id, "normal")
    system_prompt = MODE_PROMPTS[current_mode]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.text or "Привет"}
            ],
            temperature=0.9,
            max_tokens=600
        )
        reply = response.choices[0].message.content
        bot.send_message(user_id, reply)  # Убрал parse_mode

    except Exception as e:
        bot.send_message(user_id, "Что-то пошло не так… Попробуй ещё раз позже")
        print(f"AI Error: {e}")
