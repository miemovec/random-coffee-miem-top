import telebot
from telebot import types
import os
import messages
import matching
import csv
import schedule
import time
from datetime import datetime
from threading import Thread
import processing_functions
import logging
import admin_functions
from functools import wraps
import pandas as pd
import statistic_functions

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

user_states = {}
user_choices = {}
user_profile_index = {}

csv_columns = ['user_id', 'user_pair_id', 'matching_round', 'rate']
users = dict()

def not_blacklisted(func):
    @wraps(func)
    def wrapper(message_or_call, *args, **kwargs):
        chat_id = message_or_call.chat.id if hasattr(message_or_call, 'chat') else message_or_call.message.chat.id
        with open('black_list.csv', 'r', encoding='utf-8') as file:
            blacklist = {row[0] for row in csv.reader(file)}
        if str(chat_id) not in blacklist:
            return func(message_or_call, *args, **kwargs)
        else:
            print(f'Доступ запрещен для пользователя: {chat_id}')
    return wrapper

# Декоратор для пользователей, которые есть в списке администраторов
def admin_only(func):
    @wraps(func)
    def wrapper(message_or_call, *args, **kwargs):
        username = message_or_call.chat.username if hasattr(message_or_call, 'chat') else message_or_call.message.chat.username
        with open('admins.csv', 'r', encoding='utf-8') as file:
            admins = {row[0] for row in csv.reader(file)}
        if str(username) in admins:
            return func(message_or_call, *args, **kwargs)
        else:
            print(f'Пользователь {username} не является администратором.')
    return wrapper

@bot.message_handler(commands=['start', 'menu'])
@not_blacklisted
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

@bot.message_handler(commands=['fake'])
def fake(message):
    chat_id = message.chat.id
    keyboard = types.InlineKeyboardMarkup()


    html = processing_functions.user_pair_html(737718893)
    print(html)

    keyboard.add(types.InlineKeyboardButton("Оценить матчинг", callback_data="admn_admins"))
    keyboard.add(types.InlineKeyboardButton("Меню", callback_data="admn_admins"))
    file_path = '/Users/vrpivnev2h/PycharmProjects/random_coffee/miem_random_coffee/photos/737718893.jpg'
    with open(file_path, 'rb') as photo:
        bot.send_photo(chat_id=chat_id, caption=html, reply_markup=keyboard, parse_mode='html', photo=photo)


@bot.message_handler(commands=['admn'])
@admin_only
def admin_menu(message):
    chat_id = message.chat.id
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(types.InlineKeyboardButton("Администраторы", callback_data="admn_admins"))
    keyboard.add(types.InlineKeyboardButton("Новые анкеты", callback_data="admn_new_profiles"))
    keyboard.add(types.InlineKeyboardButton("Черный список", callback_data="admn_blacklist"))
    keyboard.add(types.InlineKeyboardButton("Матчинги", callback_data="last_matchings"))
    keyboard.add(types.InlineKeyboardButton("Статистика", callback_data="admn_statistics"))
    keyboard.add(types.InlineKeyboardButton("Запустить матчинг", callback_data="start_matching"))
    bot.send_message(chat_id, "Пожалуйста, выберите раздел меню администратора:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'admn')
@admin_only
def admin_menu_callback(call):
    admin_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'statistics_all_users')
def send_all_users_stats(call):
    chat_id = call.message.chat.id
    plot_file = statistic_functions.generate_all_users_stats_plot()

    with open(plot_file, 'rb') as img:
        bot.send_photo(chat_id, img)


@bot.callback_query_handler(func=lambda call: call.data == 'new_users_count')
def send_new_users_stats(call):
    chat_id = call.message.chat.id
    plot_file, table_file = statistic_functions.generate_new_users_stats()

    with open(plot_file, 'rb') as img:
        bot.send_photo(chat_id, img)

    with open(table_file, 'rb') as table:
        bot.send_document(chat_id, table)

@bot.callback_query_handler(func=lambda call: call.data == 'matching_stats')
def send_matching_stats(call):
    chat_id = call.message.chat.id
    matching_stats_list = statistic_functions.get_matching_stats()

    df_stats = pd.DataFrame(matching_stats_list)

    dir_name = 'export/history_stats'
    os.makedirs(dir_name, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = os.path.join(dir_name, f'matching_stats_{timestamp}.csv')

    df_stats.to_csv(csv_file, index=False)

    with open(csv_file, 'rb') as file:
        try:
            bot.send_document(chat_id, file)
        except:
            pass


@bot.callback_query_handler(func=lambda call: call.data == 'admn_statistics')
def statistics_menu(call):
    chat_id = call.message.chat.id

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Новые пользователи", callback_data=f"new_users_count"))
    markup.add(types.InlineKeyboardButton("Все пользователи", callback_data="statistics_all_users"))
    markup.add(types.InlineKeyboardButton("Статистика по матчингам", callback_data="matching_stats"))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="admn"))
    bot.send_message(chat_id, 'Пожалуйста, выберите раздел меню статистики:', reply_markup=markup, parse_mode='HTML')


#           старт матчинг блока
@bot.callback_query_handler(func=lambda call: call.data == 'last_matchings')
def last_matchings(call):
    chat_id = call.message.chat.id
    send_matching(chat_id, index=0)


def send_matching(chat_id, index):
    info = admin_functions.MatchingManager.get_matching_info(index)

    if not info:
        bot.send_message(chat_id, "Матчинги закончились.")
        return

    markup = types.InlineKeyboardMarkup()
    next_button = types.InlineKeyboardButton("Далее", callback_data=f"matching_next_{index + 1}")
    back_button = types.InlineKeyboardButton("Назад", callback_data="admn_matchings")
    markup.add(next_button)
    markup.add(back_button)

    text = admin_functions.MatchingManager.format_matching_info(info)
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith('matching_next_'))
def matching_next(call):
    index = int(call.data.split('_')[-1])
    chat_id = call.message.chat.id

    send_matching(chat_id, index=index)

#              конец матчинг блока

@bot.callback_query_handler(func=lambda call: call.data == 'admn_admins')
@admin_only
def admins_managment(call):
    chat_id = call.message.chat.id
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(types.InlineKeyboardButton("Полный список", callback_data="admn_admins_list"))
    keyboard.add(types.InlineKeyboardButton("Добавить", callback_data="admn_admins_add"))
    keyboard.add(types.InlineKeyboardButton("Удалить", callback_data="admn_admins_remove"))
    bot.send_message(chat_id, "<b>Управление администраторами</b>", reply_markup=keyboard, parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == "admn_admins_list")
@admin_only
def handle_admins_list(call):

    admin_manager = admin_functions.AdminManager()
    chat_id = call.message.chat.id

    if not os.path.exists(admin_manager.filename) or os.path.getsize(admin_manager.filename) == 0:
        bot.send_message(chat_id, "⚠️ Список администраторов пуст.")
        return

    with open(admin_manager.filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        admins = [f"@{row['username']}" for row in reader]

    if admins:
        admins_text = "👨‍💻 <b>Список администраторов:</b>\n\n" + "\n".join(admins)
    else:
        admins_text = "⚠️ Список администраторов пуст."

    bot.send_message(chat_id, admins_text, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'admn_admins_add')
@admin_only
def admin_add_button_handler(call):
    msg = bot.send_message(
        call.message.chat.id,
        "Отправьте данные в формате:\n\n<code>@username</code>",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_admin_add)


def process_admin_add(message):
    admin_manager = admin_functions.AdminManager()  # Инициализируем ваш класс
    chat_id = message.chat.id

    try:
        # Парсим отправленный текст
        raw_text = message.text.strip()

        if not raw_text.startswith('@'):
            raise ValueError("Имя пользователя должно начинаться с @.")

        username_to_add = raw_text[1:]  # Извлекаем username, убирая @

        # Пытаемся добавить администратора
        added = admin_manager.add_admin(username_to_add)

        if added:
            bot.send_message(
                chat_id,
                f"✅ Администратор <b>{username_to_add}</b> успешно добавлен!",
                parse_mode='HTML'
            )
        else:
            bot.send_message(
                chat_id,
                f"⚠️ Администратор <b>{username_to_add}</b> уже существует.",
                parse_mode='HTML'
            )

    except ValueError as e:
        bot.send_message(
            chat_id,
            f"❌ Ошибка формата данных.\n\nИспользуйте формат:\n<code>@username</code>",
            parse_mode='HTML'
        )
    except Exception as ex:
        bot.send_message(
            chat_id,
            f"❌ Возникла непредвиденная ошибка: {ex}",
            parse_mode='HTML'
        )


@bot.callback_query_handler(func=lambda call: call.data == 'admn_admins_remove')
@admin_only
def admin_remove_button_handler(call):
    msg = bot.send_message(
        call.message.chat.id,
        "Отправьте данные администратора, которого нужно удалить в формате:\n\n<code>@username</code>",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_admin_removal)


def process_admin_removal(message):
    admin_manager = admin_functions.AdminManager()  # Инициализируем ваш класс
    chat_id = message.chat.id

    try:
        # Парсим отправленный текст
        raw_text = message.text.strip()

        if not raw_text.startswith('@'):
            raise ValueError("Имя пользователя должно начинаться с @.")

        username_to_remove = raw_text[1:]  # Извлекаем username, убираем @

        # Пытаемся удалить администратора
        removed = admin_manager.remove_admin(username_to_remove)

        if removed:
            bot.send_message(
                chat_id,
                f"✅ Администратор <b>{username_to_remove}</b> успешно удалён!",
                parse_mode='HTML'
            )
        else:
            bot.send_message(
                chat_id,
                f"⚠️ Администратор <b>{username_to_remove}</b> не найден в списке.",
                parse_mode='HTML'
            )

    except ValueError:
        bot.send_message(
            chat_id,
            "❌ Данные должны быть в формате:\n<code>@username</code>",
            parse_mode='HTML'
        )

    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ Возникла ошибка: {e}",
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: call.data == 'admn_new_profiles')
@admin_only
def process_profiles(call):
    user_profile_index[call.from_user.id] = 0
    send_profile(call.message.chat.id, 0)

def send_profile(chat_id, index):
    user_manager = admin_functions.UserManager()
    profiles = user_manager.get_profiles()

    if not profiles or index >= len(profiles):
        bot.send_message(chat_id, "Нет новых профилей для показа.")
        return False

    profile_chat_id = int(profiles[index][0])
    stats_html = messages.user_profile(profile_chat_id, only_stats=True)
    file_path = f"photos/{profile_chat_id}.jpg"

    # Отправляем профиль (фото или текст)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=stats_html, parse_mode='HTML')
    else:
        bot.send_message(chat_id, stats_html, parse_mode='HTML')

    # Создаем кнопки
    markup = types.InlineKeyboardMarkup()

    approve_button = types.InlineKeyboardButton("Одобрить", callback_data=f'profile_approve_{profile_chat_id}_{index}')
    block_button = types.InlineKeyboardButton("Заблокировать", callback_data=f'profile_block_{profile_chat_id}_{index}')

    if index < len(profiles) - 1:
        next_button = types.InlineKeyboardButton("Далее", callback_data=f'profile_next_{profile_chat_id}_{index + 1}')
        markup.row(next_button)

    markup.row(approve_button, block_button)

    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)
    return True

@bot.callback_query_handler(func=lambda call: call.data.startswith('profile_'))
@admin_only
def handle_profile_actions(call):
    user_manager = admin_functions.UserManager()
    action, profile_chat_id, current_index = call.data.split('_')[1:]
    current_index = int(current_index)

    # Всегда обновляем список профилей после изменений
    profiles = user_manager.get_profiles()

    if action == "next":
        next_index = current_index
    elif action == "approve":
        user_manager.remove_profile(profile_chat_id)
        bot.answer_callback_query(call.id, f"Профиль {profile_chat_id} одобрен")
        profiles = user_manager.get_profiles()
        next_index = current_index  # профиль удалён, следующий встаёт на его место
    elif action == "block":
        user_manager.add_to_blacklist(profile_chat_id)
        user_manager.remove_profile(profile_chat_id)
        bot.answer_callback_query(call.id, f"Профиль {profile_chat_id} заблокирован")
        profiles = user_manager.get_profiles()
        next_index = current_index  # профиль удалён, следующий встаёт на его место
    else:
        bot.answer_callback_query(call.id, "Неизвестное действие")
        return

    # Показываем следующий профиль
    if not send_profile(call.message.chat.id, next_index):
        bot.send_message(call.message.chat.id, "Все профили просмотрены.")

## Обработчик кнопки меню "Черный список"
@bot.callback_query_handler(func=lambda call: call.data == 'admn_blacklist')
@admin_only
def blacklist_menu(call):
    chat_id = call.message.chat.id
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(types.InlineKeyboardButton("Заблокированные пользователи", callback_data='blacklist_show_0'))
    keyboard.add(types.InlineKeyboardButton("Разблокировать", callback_data='blacklist_remove'))


    bot.send_message(chat_id, "Управление черным списком:", reply_markup=keyboard)


# Показать заблокированного пользователя по индексу
@bot.callback_query_handler(func=lambda call: call.data.startswith('blacklist_show_'))
@admin_only
def show_blacklisted_users(call):
    user_manager = admin_functions.UserManager()
    blacklisted = user_manager.get_blacklisted_users()

    index = int(call.data.split('_')[-1])

    if not blacklisted or index >= len(blacklisted):
        bot.send_message(call.message.chat.id, "Черный список пуст или пользователи закончились.")
        return

    chat_id = int(blacklisted[index])
    profile_text = messages.user_profile(chat_id, only_stats=True)
    photo_path = f"photos/{chat_id}.jpg"

    markup = types.InlineKeyboardMarkup()
    if index < len(blacklisted) - 1:
        next_button = types.InlineKeyboardButton("Далее", callback_data=f'blacklist_show_{index + 1}')
        markup.add(next_button)

    unblock_button = types.InlineKeyboardButton("Разблокировать", callback_data=f'unblock_{chat_id}_{index}')
    markup.add(unblock_button)

    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo, caption=profile_text, parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, profile_text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('unblock_'))
@admin_only
def unblock_user(call):
    _, chat_id, current_index = call.data.split('_')
    user_manager = admin_functions.UserManager()

    if user_manager.remove_from_blacklist(chat_id):
        bot.answer_callback_query(call.id, "Пользователь успешно разблокирован.")
        bot.send_message(call.message.chat.id, "Пользователь разблокирован.")
    else:
        bot.answer_callback_query(call.id, "Пользователь не найден в черном списке.")

    # Проверяем наличие следующего пользователя
    blacklisted = user_manager.get_blacklisted_users()
    next_index = int(current_index)

    if next_index < len(blacklisted):
        # Показываем следующий профиль
        show_blacklisted_users(types.CallbackQuery(
            id=call.id,
            from_user=call.from_user,
            message=call.message,
            data=f'blacklist_show_{next_index}'
        ))
    else:
        bot.send_message(call.message.chat.id, "Черный список пуст или пользователи закончились.")


# Ожидание username для разблокировки
@bot.callback_query_handler(func=lambda call: call.data == 'blacklist_remove')
@admin_only
def remove_from_blacklist_prompt(call):
    msg = bot.send_message(call.message.chat.id, "Отправьте username пользователя для разблокировки (в формате @username):")
    bot.register_next_step_handler(msg, remove_from_blacklist)


def remove_from_blacklist(message):
    username = message.text.strip().lstrip('@')
    user_manager = admin_functions.UserManager()

    chat_id = user_manager.get_chat_id_by_username(username)

    if not chat_id:
        bot.send_message(message.chat.id, "Пользователь не найден.")
        return

    if user_manager.remove_from_blacklist(chat_id):
        bot.send_message(message.chat.id, f"Пользователь @{username} успешно разблокирован.")
    else:
        bot.send_message(message.chat.id, f"Пользователь @{username} не был в черном списке.")


@bot.callback_query_handler(func=lambda call: call.data == 'rewrite_profile')
@not_blacklisted
def start_interests(call):
    chat_id = call.message.chat.id
    user_states[chat_id] = iter(categories.keys())
    user_choices[chat_id] = {}
    send_next_category(chat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
@not_blacklisted
def select_option(call):
    chat_id = call.message.chat.id
    option_raw = call.data.split("select_", 1)[1]
    try:
        category = user_choices[chat_id]['current_category']
    except KeyError:
        processing_functions.design_menue(chat_id)
        return

    # Для длинных категорий будем использовать индекс, иначе строку
    if category in ["Специализация", "Глобальные интересы"]:
        idx = int(option_raw)
        option = categories[category][idx]
    else:
        option = option_raw

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

    # тоже самое построение клавиатуры здесь
    if category in ["Специализация", "Глобальные интересы"]:
        for idx, opt in enumerate(categories[category]):
            status = "✅" if opt in user_choices[chat_id][category] else "❌"
            keyboard.add(types.InlineKeyboardButton(f"{opt} {status}", callback_data=f"select_{idx}"))
    else:
        for opt in categories[category]:
            status = "✅" if opt in user_choices[chat_id][category] else "❌"
            keyboard.add(types.InlineKeyboardButton(f"{opt} {status}", callback_data=f"select_{opt}"))

    keyboard.add(types.InlineKeyboardButton("Далее", callback_data="next"))
    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=keyboard)
    except Exception as ex:
        print(ex)


@bot.callback_query_handler(func=lambda call: call.data == 'next')
@not_blacklisted
def next_category(call):
    chat_id = call.message.chat.id
    try:
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
    except Exception as ex:
        processing_functions.design_menue(chat_id)
        return
    try:
        send_next_category(chat_id)
    except StopIteration:
        bot.send_message(chat_id, "Введите ваш возраст:")
        user_choices[chat_id]['awaiting_age'] = True


@bot.message_handler(func=lambda message: user_choices.get(message.chat.id, {}).get('awaiting_age', False))
@not_blacklisted
def handle_age_input(message):
    chat_id = message.chat.id
    try:
        age = int(message.text)
        if 18 < age < 70:
            user_choices[chat_id]['Возраст'] = age
            user_choices[chat_id].pop('awaiting_age', None)
            bot.send_message(chat_id, "Ваши выбранные интересы:")
            summary = "\n".join([
                f"<b>{cat}</b>: {', '.join(choices) if isinstance(choices, list) else choices}"
                for cat, choices in user_choices[chat_id].items()
                if cat not in ['current_category', 'awaiting_age']
            ])
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))
            bot.send_message(chat_id, summary, reply_markup=markup, parse_mode='html')
            processing_functions.save_user_choices(chat_id, user_choices[chat_id])
            users_manager = admin_functions.UserManager()
            users_manager.updated_profile(chat_id)
            user_states.pop(chat_id, None)
            user_choices.pop(chat_id, None)
        else:
            bot.send_message(chat_id, "Пожалуйста, введите корректный возраст")
    except Exception as ex:
        logging.error(ex)
        bot.send_message(chat_id, "Пожалуйста, введите ваш возраст числом.")


@bot.message_handler(func=lambda message: not message.from_user.is_bot)
@not_blacklisted
def text_handler(message):
    bot.send_message(message.chat.id, 'Текст не распознан')
    profile_markup = types.InlineKeyboardMarkup()
    profile_markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=profile_markup)


@bot.callback_query_handler(func=lambda call: call.data == 'photo')
@not_blacklisted
def handle_query(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Пожалуйста, отправьте вашу фотографию.")
    bot.register_next_step_handler_by_chat_id(chat_id, processing_functions.receive_photo)


@bot.callback_query_handler(func=lambda call: call.data == 'profile')
@not_blacklisted
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
@not_blacklisted
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
@not_blacklisted
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
        bot.send_message(callback.message.chat.id, 'Матчинг запущен', parse_mode='html')

def send_next_category(chat_id):
    """Отправляет следующий этап выбора."""
    try:
        category = next(user_states[chat_id])
        user_choices[chat_id]['current_category'] = category

        keyboard = types.InlineKeyboardMarkup()

        if category in ["Специализация", "Глобальные интересы"]:
            for idx, option in enumerate(categories[category]):
                keyboard.add(types.InlineKeyboardButton(option, callback_data=f"select_{idx}"))
        else:
            for option in categories[category]:
                keyboard.add(types.InlineKeyboardButton(option, callback_data=f"select_{option}"))

        keyboard.add(types.InlineKeyboardButton("Далее", callback_data="next"))
        bot.send_message(chat_id, f"Выберите {category}:", reply_markup=keyboard)
    except StopIteration:
        bot.send_message(chat_id, "Введите ваш возраст:")
        user_choices[chat_id]['awaiting_age'] = True
    except KeyError:
        processing_functions.design_menue(chat_id)



def run_schedule():
    schedule.every().sunday.at("10:00").do(matching.perform_matching)
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_scheduled_tasks():
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()

def clear_old_updates():
    updates = bot.get_updates(offset=-1)  # Получаем последнее обновление
    if updates:
        last_update_id = updates[-1].update_id
        bot.get_updates(offset=last_update_id + 1)  # Пропускаем все старые обновления

if __name__ == '__main__':
    clear_old_updates()
    start_scheduled_tasks()
    bot.polling()
