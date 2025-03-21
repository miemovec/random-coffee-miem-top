import pandas as pd
from telebot import types
import os
import messages
from main import bot
from messages import user_pair_html, user_profile
import statistic_functions

def ask_question(message_id, user_id, pair_id, matching_round, question, current_question):
    markup = types.InlineKeyboardMarkup()
    if current_question != 1:
        answer_prefix = '<b>Оцените по шкале от 1 до 5</b>\n'
        message_text = "{}Вопрос №{}: {}".format(answer_prefix, current_question + 1, question)
        for i in range(1, 6):
            markup.add(types.InlineKeyboardButton(text=str(i), callback_data="qst:{}&{}&{}&{}&{}".format(user_id, pair_id, matching_round, current_question, i)))
    else:
        answers = [
            'Людей с похожими интересами',
            'Людей из другой области',
            'Случайных людей'
        ]
        for i,answer in enumerate(answers):
            markup.add(types.InlineKeyboardButton(text=answer, callback_data="qst:{}&{}&{}&{}&{}".format(user_id, pair_id, matching_round, current_question, i+1)))
        message_text = "Вопрос №{}: {}".format(current_question + 1, question)
    if message_id is None:
        message = bot.send_message(user_id, message_text, reply_markup=markup, parse_mode='html')
        return message.message_id
    elif current_question == 3:
        markup.add(types.InlineKeyboardButton(text='Не общались', callback_data="qst:{}&{}&{}&{}&{}".format(user_id, pair_id, matching_round, current_question, 6)))
        bot.edit_message_text(chat_id=user_id, message_id=message_id,
                              text=message_text, reply_markup=markup, parse_mode='html')
        return message_id
    elif current_question == 4:
        bot.edit_message_text(chat_id=user_id, message_id=message_id,
                              text="Ваши ответы сохранены, спасибо за обратную связь !")
    else:
        try:
            bot.edit_message_text(chat_id=user_id, message_id=message_id, text=message_text, reply_markup=markup, parse_mode='html')
            return message_id
        except Exception as ex:
            print(ex)


def sent_messages(matches_df, users_file='all_users.csv'):
    possible_questions = [
        'Насколько вас устроил возраст собеседника?',
        'Вы хотели бы чтобы в будущем мы рекомендовали вам',
        'Насколько совпали ли ваши интересы?',
        'Насколько интересен собеседник?'
    ]

    if matches_df.empty:
        return


    latest_matching_num = matches_df['matching_num'].max()
    latest_matches = matches_df[matches_df['matching_num'] == latest_matching_num]
    all_users = set(latest_matches['User 1']).union(set(latest_matches['User 2']))  # Все уникальные участники
    real_users = [user for user in all_users if not str(user).startswith('synthetic_user')]  # Настоящие пользователи


    for real_user in real_users:
        match_rows = latest_matches[(latest_matches['User 1'] == real_user) | (latest_matches['User 2'] == real_user)]
        if match_rows.empty:
            continue  # Если пользователя нет в последних парах, пропускаем


        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))

        messages = []
        for _, row in match_rows.iterrows():
            pair_id = row['User 2'] if row['User 1'] == real_user else row['User 1']
            pair_html = user_pair_html(pair_id, users_file)
            messages.append((pair_html,pair_id))


        for message in messages:
            pair_id = message[1]
            file_path = f'photos/{int(pair_id)}.jpg'
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as photo:
                        bot.send_photo(chat_id=real_user, photo=photo, caption=message[0], reply_markup=markup, parse_mode='html')
                else:
                    bot.send_message(
                        chat_id=real_user,
                        text=message[0],
                        reply_markup=markup,
                        parse_mode='html'
                    )
                ask_question(None, int(real_user), int(pair_id), latest_matching_num, possible_questions[0], 0)
            except Exception as ex:
                print(ex, real_user)


def check_participant(chat_id):
    file_path = 'participants.csv'
    if not os.path.exists(file_path):
        return False

    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        return False

    if 'chat_id' not in df.columns:
        return False

    return chat_id in df['chat_id'].values


def add_participant(chat_id):
    file_path = 'all_users.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        return None

    user = df[df['chat_id'] == chat_id]

    if user.empty:
        return None


    user_data = user.iloc[0]
    if pd.isnull(user_data['sex']):
        return None
    file_path = 'participants.csv'
    if not os.path.exists(file_path):
        df = pd.DataFrame({'chat_id': [chat_id]})
        df.to_csv(file_path, index=False)
        return "Пользователь успешно добавлен."


    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame({'chat_id': []})


    if str(chat_id) in df['chat_id'].values:
        return "Пользователь уже существует."

    new_row = pd.DataFrame({'chat_id': [chat_id]})
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(file_path, index=False)
    return "Пользователь успешно добавлен."


def remove_participant(chat_id, file_path='participants.csv'):
    if not os.path.exists(file_path):
        return "Файл участников отсутствует."


    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        return "Файл участников пуст."

    if chat_id not in df['chat_id'].values:
        return "Пользователь не найден."

    df = df[df['chat_id'] != chat_id]

    df.to_csv(file_path, index=False)
    return "Пользователь успешно удален."


def add_new_user(
        file_path, chat_id=None, user_id=None, name=None, age=None, sex=None, pair_sex=None,
        university_group=None, specialization=None, photo=None, username=None, tags=None
):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=[
            "chat_id", "user_id", "name", "age", "sex", "pair_sex", "university_group",
            "specialization", "photo", "username", "tags"
        ])
    # Проверка, есть ли уже пользователь с таким chat_id
    if df[(df['chat_id'] == chat_id)].empty:
        statistic_functions.log_user_registration(chat_id=chat_id, username = username)
        user_dict = {
            'chat_id': chat_id,
            'user_id': user_id,
            'name': name,
            'age': age,
            'sex': sex,
            'pair_sex': pair_sex,
            'university_group': university_group,
            'specialization': specialization,
            'photo': photo,
            'username': username,  # Сохраняем имя пользователя
            'tags': tags
        }

        df = pd.concat([df, pd.DataFrame([user_dict])], ignore_index=True)
        df.to_csv(file_path, index=False)

    return df


def receive_photo(message):
    if message.content_type == 'photo':
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        chat_id = message.chat.id
        with open(f'photos/{chat_id}.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)
        chat_id = message.chat.id
        file_path = f"photos/{chat_id}.jpg"
        stats_html = user_profile(message.chat.id)
        menu_markup = types.InlineKeyboardMarkup()
        menu_markup.add(types.InlineKeyboardButton('Изменить', callback_data='rewrite_profile'))
        menu_markup.add(types.InlineKeyboardButton('Фото', callback_data='photo'))
        menu_markup.add(types.InlineKeyboardButton('Меню', callback_data='menu'))
        if os.path.exists(file_path):
            with open(file_path, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=stats_html, parse_mode='html', reply_markup=menu_markup)
        else:
            bot.send_message(chat_id, text=stats_html, parse_mode='html', reply_markup=menu_markup)
    else:
        bot.send_message(message.chat.id, "Это не фотография, попробуйте снова.")
        design_menue(message.chat.id)


def design_menue(chat_id):
    participant = check_participant(chat_id)
    participant_callback = " ".join(['participate', str(participant)])
    markup = types.InlineKeyboardMarkup()
    if participant:
        text = messages.menu_text_html(True)
        markup.add(types.InlineKeyboardButton('Остановить участие', callback_data=participant_callback))
    else:
        text = messages.menu_text_html(False)
        markup.add(types.InlineKeyboardButton('Участвовать', callback_data=participant_callback))


    markup.add(types.InlineKeyboardButton('Профиль', callback_data='profile'))

    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='html')


def save_user_choices(chat_id, choices):
    filename = 'all_users.csv'
    new_data = {k: v for k, v in choices.items() if k not in ['current_category', 'awaiting_age']}
    if 'Пол' in new_data:
        new_data['sex'] = new_data.pop('Пол')[0]
    if 'Пол собеседника' in new_data:
        new_data['pair_sex'] = new_data.pop('Пол собеседника')[0]
    if 'Специализация' in new_data:
        new_data['specialization'] = [new_data.pop('Специализация')]
    if 'Возраст' in new_data:
        new_data['age'] = new_data.pop('Возраст')


    tags = []
    for category, selected in new_data.items():
        if category not in ['sex', 'pair_sex', 'specialization', 'age']:
            if isinstance(selected, list):
                tags.extend(selected)
    new_data['tags'] = [tags]
    new_data['university_group'] = None
    new_data['chat_id'] = chat_id


    keys = ['chat_id', 'sex', 'pair_sex', 'specialization', 'age', 'tags', 'university_group']
    if os.path.exists(filename):
        df = pd.read_csv(filename)
    else:
        df = pd.DataFrame(columns=keys)
    filtered_data = {key: value for key, value in new_data.items() if key in keys}
    if str(chat_id) in df['chat_id'].astype(str).values:
        filtered_data = pd.DataFrame(filtered_data)

        matching_indices = df[df['chat_id'] == chat_id].index.tolist()[0]
        df.loc[matching_indices, keys] = filtered_data.loc[0, keys]

    else:
        new_row = {column: filtered_data.get(column, None) for column in df.columns}
        new_row['chat_id'] = chat_id
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(filename, index=False, encoding='utf-8')
