import telebot
from telebot import types
import os
import messages
import matching
import csv
import schedule
import time
from threading import Thread
import processing_functions
import logging

bot = telebot.TeleBot('7538044848:AAHmfq5f63GWyU4Fp7judnr36JxjIo3t41s')


categories = {
    "Пол": ["мужской", "женский"],
    "Пол собеседника": ["мужской", "женский", "не важно"],
    "Специализация": [
        "Информатика и вычислительная техника", "Прикладная математика", "Информационная безопасность",
        "Инфокоммуникационные технологии и системы связи", "Компьютерная безопасность",
        "Компьютерные системы и сети", "Интернет вещей и киберфизические системы",
        "Информационная безопасность и технологии искусственного интеллекта", "Кибербезопасность",
        "Системный анализ и математические технологии", "Прикладная электроника и фотоника",
        "Прикладные модели искусственного интеллекта", "Аппаратно-программные комплексы искусственного интеллекта",
        "Информационная безопасность в кредитно-финансовой сфере", "Я преподаватель"
    ],
    "Глобальные интересы": [
        "Гуманитарные и социальные науки", "Бизнес и право", "Медицина и здоровье", "Образование и педагогика",
        "Инженерия", "Программирование", "Дизайн", "Психология"
    ],
    "Спорт": [
        "Спортзал", "Футбол", "Баскетбол", "Волейбол", "Плавание", "Теннис", "Бег", "Йога", "Лыжи и сноуборд",
        "Велоспорт", "Скейтбординг", "Сёрфинг", "Боевые искусства"
    ],
    "Хобби": [
        "Фильмы", "Сериалы", "Аниме", "Вязание", "Рисование", "Фотография", "Кулинария", "Танцы",
        "Музыка", "Настольные игры", "Путешествия", "Садоводство", "Видеоигры", "Любитель кошек", "Прогулки с собаками"
    ],
    "Интересы в IT": [
        "Frontend", "Backend", "Mobile", "ML", "HR", "Аналитика", "Краш-тест идей", "Продукты и проекты",
        "Дизайн/UX", "PR и маркетинг", "Тренды рынка", "Обучение и развитие", "Новости компании", "Хобби и увлечения",
        "QA", "Геймдев", "Развитие бизнеса", "Переговоры и продажи", "DevOps/SRE"
    ],
    "Здоровье": [
        "Здоровое питание", "Медитация", "Ментальное здоровье", "Фитнес и тренировки", "ЗОЖ"
    ]
}

user_states = {}  # Состояние пользователя
user_choices = {}  # Выбранные пользователем варианты

specialization_mapping = {index: spec for index, spec in enumerate(categories["Специализация"])}
global_interest_mapping = {index: interest for index, interest in enumerate(categories["Глобальные интересы"])}


csv_columns = ['user_id', 'user_pair_id', 'matching_round', 'rate']
users = dict()


@bot.message_handler(commands=['start', 'menu'])
def start_command(message):
    if not message.from_user.is_bot:
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        username = message.chat.username
        processing_functions.add_new_user(file_path='all_users.csv', chat_id=chat_id, user_id=user_id, name=user_name, username=username)
    else:
        chat_id = message.chat_id
    processing_functions.design_menue(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == 'rewrite_profile')
def start_interests(call):
    chat_id = call.message.chat.id
    user_states[chat_id] = iter(categories.keys())
    user_choices[chat_id] = {}
    send_next_category(chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_specialization_"))
def select_specialization(call):
    chat_id = call.message.chat.id
    idx = int(call.data.split("select_specialization_", 1)[1])
    specialization = specialization_mapping[idx]

    user_choices[chat_id]["Специализация"] = [specialization]

    keyboard = types.InlineKeyboardMarkup()
    for idx, spec in specialization_mapping.items():
        status = "✅" if spec in user_choices[chat_id]["Специализация"] else "❌"
        keyboard.add(types.InlineKeyboardButton(f"{spec} {status}", callback_data=f"select_specialization_{idx}"))

    keyboard.add(types.InlineKeyboardButton("Далее", callback_data="next"))
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_global_interest_"))
def select_global_interest(call):
    chat_id = call.message.chat.id
    idx = int(call.data.split("select_global_interest_", 1)[1])
    global_interest = global_interest_mapping[idx]

    user_choices[chat_id]["Глобальные интересы"] = [global_interest]

    keyboard = types.InlineKeyboardMarkup()
    for idx, interest in global_interest_mapping.items():
        status = "✅" if interest in user_choices[chat_id]["Глобальные интересы"] else "❌"
        keyboard.add(types.InlineKeyboardButton(f"{interest} {status}", callback_data=f"select_global_interest_{idx}"))

    keyboard.add(types.InlineKeyboardButton("Далее", callback_data="next"))
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def select_option(call):
    chat_id = call.message.chat.id
    option = call.data.split("select_", 1)[1]
    category = user_choices[chat_id]['current_category']

    if category in ["Пол", "Пол собеседника"]:
        user_choices[chat_id][category] = [option]
    else:
        if category not in user_choices[chat_id]:
            user_choices[chat_id][category] = []

        if option in user_choices[chat_id][category]:
            user_choices[chat_id][category].remove(option)
        else:
            user_choices[chat_id][category].append(option)


    keyboard = types.InlineKeyboardMarkup()
    for opt in categories[category]:
        status = "✅" if opt in user_choices[chat_id][category] else "❌"
        keyboard.add(types.InlineKeyboardButton(f"{opt} {status}", callback_data=f"select_{opt}"))

    keyboard.add(types.InlineKeyboardButton("Далее", callback_data="next"))
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'next')
def next_category(call):
    chat_id = call.message.chat.id
    current_category = user_choices[chat_id].get('current_category')

    if current_category == "Пол" and "Пол" not in user_choices[chat_id]:
        bot.answer_callback_query(call.id, "Пожалуйста, обязательно выберите ваш пол.")
        return
    if current_category == "Пол собеседника" and "Пол собеседника" not in user_choices[chat_id]:
        bot.answer_callback_query(call.id, "Пожалуйста, обязательно выберите пол собеседника.")
        return
    if current_category == "Специализация" and "Специализация" not in user_choices[chat_id]:
        bot.answer_callback_query(call.id, "Пожалуйста, обязательно выберите вашу специализацию.")
        return

    try:
        send_next_category(chat_id)
    except StopIteration:
        bot.send_message(chat_id, "Введите ваш возраст:")
        user_choices[chat_id]['awaiting_age'] = True


@bot.message_handler(func=lambda message: user_choices.get(message.chat.id, {}).get('awaiting_age', False))
def handle_age_input(message):
    chat_id = message.chat.id
    try:
        age = int(message.text)
        if 18 < age < 70:
            user_choices[chat_id]['age'] = age
            user_choices[chat_id].pop('awaiting_age', None)
            bot.send_message(chat_id, "Ваши выбранные интересы:")
            summary = "\n".join([
                f"{cat}: {', '.join(choices) if isinstance(choices, list) else choices}"
                for cat, choices in user_choices[chat_id].items()
                if cat not in ['current_category', 'awaiting_age']
            ])
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))
            bot.send_message(chat_id, summary, reply_markup=markup)
            processing_functions.save_user_choices(chat_id, user_choices[chat_id])
            user_states.pop(chat_id, None)
            user_choices.pop(chat_id, None)
        else:
            bot.send_message(chat_id, "Пожалуйста, введите корректный возраст")
    except Exception as ex:
        logging.error(ex)
        bot.send_message(chat_id, "Пожалуйста, введите ваш возраст числом.")


@bot.message_handler(func=lambda message: not message.from_user.is_bot)
def text_handler(message):
    bot.send_message(message.chat.id, 'Текст не распознан')
    profile_markup = types.InlineKeyboardMarkup()
    profile_markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=profile_markup)


@bot.callback_query_handler(func=lambda call: call.data == 'photo')
def handle_query(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Пожалуйста, отправьте вашу фотографию.")
    bot.register_next_step_handler_by_chat_id(chat_id, processing_functions.receive_photo)


@bot.callback_query_handler(func=lambda call: call.data == 'profile')
def send_user_profile(call):
    chat_id = call.message.chat.id
    file_path = f"photos/{chat_id}.jpg"
    stats_html = messages.user_profile(call.message.chat.id)
    menu_markup = types.InlineKeyboardMarkup()
    menu_markup.add(types.InlineKeyboardButton('Изменить', callback_data='rewrite_profile'))
    menu_markup.add(types.InlineKeyboardButton('Фото', callback_data='photo'))
    menu_markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))
    if os.path.exists(file_path):
        with open(file_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption = stats_html, parse_mode= 'html', reply_markup=menu_markup)
    else:
        bot.send_message(chat_id, text = stats_html, parse_mode= 'html', reply_markup=menu_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('qst:'))
def handle_query(call):

    possible_questions = [
        'Насколько вас устроил возраст собеседника?',
        'Вы хотели бы чтобы в будущем мы рекомендовали вам',
        'Насколько совпали ли ваши интересы?',
        'Насколько интересен собеседник?'
    ]

    data = call.data[4:]
    user_id, pair_id, matching_round, current_question, answer = map(int, data.split('&'))

    if user_id not in users:
        users[user_id] = dict()
    if pair_id not in users[user_id]:
        users[user_id][pair_id] = dict()
    if matching_round not in users[user_id][pair_id]:
        users[user_id][pair_id][matching_round] = []

    user_round_data = users[user_id][pair_id][matching_round]
    user_round_data.append(answer)

    if current_question == 3:
        bot.answer_callback_query(call.id, "Спасибо за ваш ответ! Вот следующий вопрос.")

        with open('matching_rate.csv', 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writerow({
                'user_id': user_id,
                'user_pair_id': pair_id,
                'matching_round': matching_round,
                'rate': user_round_data
            })
            message_id = call.message.message_id
            processing_functions.ask_question(message_id, user_id, pair_id, matching_round, None, current_question + 1)
        return

    message_id = call.message.message_id
    next_question = possible_questions[current_question + 1]
    processing_functions.ask_question(message_id, user_id, pair_id, matching_round, next_question, current_question + 1)


@bot.callback_query_handler(func=lambda callback: True)
def callback_handler(callback):
    data = callback.data.split(' ')
    callback_data = data[0]
    if callback_data == 'menu':
        processing_functions.design_menue(callback.message.chat.id)
    elif callback_data == 'profile':
        stats_html = messages.user_profile(callback.message.chat.id)
        menu_markup = types.InlineKeyboardMarkup()
        menu_markup.add(types.InlineKeyboardButton('Изменить', callback_data='rewrite_profile'))
        menu_markup.add(types.InlineKeyboardButton('Фото', callback_data='photo'))
        menu_markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))
        bot.send_message(callback.message.chat.id, stats_html, parse_mode='html', reply_markup=menu_markup)
    elif callback_data == 'participate':
        participant = data[1]
        markup = types.InlineKeyboardMarkup()
        if participant == 'True':
            participant = 'False'
            participant_callback = " ".join(['participate', str(participant)])
            processing_functions.remove_participant(callback.message.chat.id)
            text = messages.menu_text_html(False)
            markup.add(types.InlineKeyboardButton('Участвовать', callback_data=participant_callback))
        else:
            participant = 'True'
            participant_callback = " ".join(['participate', str(participant)])
            result = processing_functions.add_participant(callback.message.chat.id)
            if result is None:
                bot.send_message(chat_id=callback.message.chat.id, text="<b>Заполните анкету, чтобы принять участие:</b>", parse_mode='html', reply_markup=markup)
                start_interests(callback)
                return None
            text = messages.menu_text_html(True)
            markup.add(types.InlineKeyboardButton('Остановить участние', callback_data=participant_callback))
        markup.add(types.InlineKeyboardButton('Профиль', callback_data='profile'))
        bot.edit_message_text(message_id =callback.message.id ,chat_id=callback.message.chat.id, text=text, parse_mode='html', reply_markup=markup)
    elif callback_data == 'start_matching':
        matching.perform_matching()


def send_next_category(chat_id):
    """Отправляет следующий этап выбора."""
    try:
        category = next(user_states[chat_id])
        user_choices[chat_id]['current_category'] = category

        keyboard = types.InlineKeyboardMarkup()
        if category == "Специализация":
            for idx, spec in specialization_mapping.items():
                keyboard.add(types.InlineKeyboardButton(spec, callback_data=f"select_specialization_{idx}"))
        elif category == "Глобальные интересы":
            for idx, interest in global_interest_mapping.items():
                keyboard.add(types.InlineKeyboardButton(interest, callback_data=f"select_global_interest_{idx}"))
        else:
            for option in categories[category]:
                keyboard.add(types.InlineKeyboardButton(option, callback_data=f"select_{option}"))

        keyboard.add(types.InlineKeyboardButton("Далее", callback_data="next"))
        bot.send_message(chat_id, f"Выберите {category}:", reply_markup=keyboard)
    except StopIteration:
        bot.send_message(chat_id, "Введите ваш возраст:")
        user_choices[chat_id]['awaiting_age'] = True


def run_schedule():
    schedule.every().sunday.at("10:00").do(matching.perform_matching)
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_scheduled_tasks():
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()


if __name__ == '__main__':
    start_scheduled_tasks()
    bot.polling()
