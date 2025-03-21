from datetime import datetime, timedelta
import textwrap
import pandas as pd

def next_sunday():
    today = datetime.today()
    days_ahead = 6 - today.weekday()  # Воскресенье = 6
    if days_ahead <= 0:
        days_ahead += 7
    next_sunday_date = today + timedelta(days=days_ahead)
    return next_sunday_date


def menu_text_html(participate):
    # Текущая дата
    current_date = datetime.today().strftime('%d %B %Y')

    # Дата следующего раунда
    next_round_date = next_sunday().strftime('%d %B %Y')

    # Определяем статус в зависимости от участия
    status = "🟢 УЧАСТВУЮ" if participate else "🔴 НЕ УЧАСТВУЮ"

    # Блоки текста
    blocks = [
        "<b>Random Coffee</b>\n",
        ("Основной вариант встреч для всех студентов и преподавателей "
         "Миэма. Наш умный алгоритм будет регулярно "
         "подбирать и присылать встречи с интересными "
         "именно вам собеседниками."),
        "Встречи проходят раз в неделю.\n",
        "<b>Следующий раунд:</b>\n",
        next_round_date + "\n",
        "<b>Статус:</b>\n",
        status + "\n",
        f"Текущая дата: {current_date}"
    ]

    formatted_blocks = []
    for block in blocks:
        if not block.startswith("<b>") and "\n" not in block:
            formatted_blocks.append(textwrap.fill(block, width=44))
        else:
            formatted_blocks.append(block)

    formatted_text = "\n".join(formatted_blocks)

    return formatted_text


def user_pair_html(user_id, users_file='all_users.csv'):
    """
    Возвращает HTML с характеристиками пары для пользователя по его user_id.
    """
    try:
        users = pd.read_csv(users_file)
    except FileNotFoundError:
        return "<b>Ошибка:</b> Файл с данными пользователей не найден."


    user_data = users[users['chat_id'] == user_id]
    if user_data.empty:
        return "<b>Ошибка:</b> Данные пользователя не найдены."

    user_data = user_data.iloc[0]

    html_content = (
        f"<b>Ваш собеседник:</b>\n\n"
        f"<b>Имя:</b> {user_data['name']}\n"
        f"<b>Возраст:</b> {int(user_data['age'])}\n"
        f"<b>Пол:</b> {'Мужчина' if user_data['sex'] == 'мужской' else 'Женщина'}\n"
        f"<b>Образовательная программа:</b> {', '.join(eval(user_data['specialization'])) if pd.notnull(user_data['specialization']) else 'Не указано'}\n"
        f"<b>Интересы:</b> {', '.join(eval(user_data['tags'])) if pd.notnull(user_data['tags']) else 'Не указано'}\n\n"
        f"<b>telegram:</b> @{user_data['username']}"
    )
    return html_content


def user_profile(chat_id, file_path='all_users.csv', only_stats=False):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        return "<b>Ошибка:</b> Файл с данными не найден."
    user = df[df['chat_id'] == chat_id]

    if user.empty:
        return "<b>Ошибка:</b> Пользователь не найден."

    user_data = user.iloc[0]

    if pd.isnull(user_data['sex']):
        return (
            f"<b>Ваша анкета:</b>\n\n"
            f"<b>Статус:</b> Анкета пустая.\n"
            f"Пожалуйста, заполните анкету для отображения профиля."
        )

    if only_stats:
        html_content = (
            f"<b>Имя:</b> {user_data['name']}\n"
            f"<b>Возраст:</b> {int(user_data['age'])}\n"
            f"<b>Пол:</b> {user_data['sex']}\n"
            f"<b>Образовательная программа:</b> {', '.join(eval(user_data['specialization'])) if pd.notnull(user_data['specialization']) else 'Не указано'}\n"
            f"<b>Интересы:</b> {', '.join(eval(user_data['tags'])) if pd.notnull(user_data['tags']) else 'Не указано'}\n"
            f"<b>Телеграм:</b> @{user_data['username']}\n"
        )
    else:
        html_content = (
            f"<b>Ваш профиль:</b>\n\n"
            f"<b>Имя:</b> {user_data['name']}\n"
            f"<b>Возраст:</b> {int(user_data['age'])}\n"
            f"<b>Пол:</b> {user_data['sex']}\n"
            f"<b>Образовательная программа:</b> {', '.join(eval(user_data['specialization'])) if pd.notnull(user_data['specialization']) else 'Не указано'}\n"
            f"<b>Интересы:</b> {', '.join(eval(user_data['tags'])) if pd.notnull(user_data['tags']) else 'Не указано'}"
        )


    return html_content

def change_photo_text():
    text = 'Пришлите фото профиля, которое увидит ваш собеседник'
    return text


