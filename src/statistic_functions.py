import csv
import os
from datetime import datetime
import pandas as pd
import pandas as pd
import plotly.graph_objects as go
from telebot import types
import os
from datetime import datetime
import ast
import plotly.express as px

def generate_new_users_stats():
    dir_name = 'export/history_stats'
    os.makedirs(dir_name, exist_ok=True)

    df = pd.read_csv('registration_log.csv', parse_dates=['registration_time'])

    df['date'] = df['registration_time'].dt.date
    users_per_day = df.groupby('date').size().reset_index(name='new_users')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    plot_file = os.path.join(dir_name, f'new_users_plot_{timestamp}.png')
    table_file = os.path.join(dir_name, f'new_users_table_{timestamp}.csv')

    fig = px.bar(users_per_day, x='date', y='new_users',
                 title="Количество новых пользователей по дням",
                 labels={'date': 'Дата', 'new_users': 'Количество новых пользователей'},
                 text='new_users')  # Добавление подписей на столбцы


    fig.update_xaxes(tickangle=45)

    fig.write_image(plot_file)

    users_per_day.to_csv(table_file, index=False)

    return plot_file, table_file

def log_user_registration(chat_id, username, log_file='registration_log.csv'):
    file_exists = os.path.isfile(log_file) and os.path.getsize(log_file) > 0

    with open(log_file, mode='a', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['chat_id', 'username', 'registration_time'])

        # Если файл пустой или не существует, пишем заголовок
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'chat_id': chat_id,
            'username': username,
            'registration_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

def generate_all_users_stats_plot(log_file='matching_log.csv'):
    dir_name = 'export/history_stats'
    os.makedirs(dir_name, exist_ok=True)

    df = pd.read_csv(log_file)

    df['date_matching'] = df['timestamp'].astype(str).str[:10] + ' (#' + df['matching_num'].astype(str) + ')'
    df['participants'] = df['participants']
    df['non_participants'] = df['all_users'] - df['participants']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['date_matching'],
        y=df['participants'],
        name='Участвует',
        marker_color='lightpink'
    ))

    fig.add_trace(go.Bar(
        x=df['date_matching'],
        y=df['non_participants'],
        name='Не участвует',
        marker_color='lightgray'
    ))

    fig.update_layout(
        title='Статистика участия пользователей в матчингe',
        xaxis_title='Дата и номер матчинга',
        yaxis_title='Количество пользователей',
        barmode='stack'
    )

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plot_file = os.path.join(dir_name, f'all_users_stats_{timestamp}.png')

    fig.write_image(plot_file)

    return plot_file

def get_matching_stats():
    matching_log_df = pd.read_csv('matching_log.csv')
    matches_df = pd.read_csv('matches.csv')

    matching_stats_list = []

    for _, row in matching_log_df.sort_values(by='matching_num', ascending=False).iterrows():
        matching_num = row['matching_num']
        date = row['timestamp'][:10]
        tag_weights = ast.literal_eval(row['tag_weights'])

        matching_scores = matches_df[matches_df['matching_num'] == matching_num]['Similarity']

        mean_score = matching_scores.mean()
        max_score = matching_scores.max()
        min_score = matching_scores.min()

        stats = {
            'matching_num': matching_num,
            'matching_date': date,
            'all_users': row['all_users'],
            'participants': row['participants'],
            'mean_score': mean_score,
            'max_score': max_score,
            'min_score': min_score,
            'tag_weights': tag_weights
        }

        matching_stats_list.append(stats)

    return matching_stats_list


def matching_log(matching_num, tag_weights, all_users_file='all_users.csv', participants_file='participants.csv', log_file='matching_log.csv'):
    # Читаем файл all_users.csv и считаем уникальных пользователей по chat_id
    all_users_df = pd.read_csv(all_users_file)
    unique_users_count = all_users_df['chat_id'].nunique()


    participants_df = pd.read_csv(participants_file)
    unique_participants_count = participants_df['chat_id'].nunique()

    stats = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'all_users': unique_users_count,
        'participants': unique_participants_count,
        'matching_num': matching_num,
        'tag_weights': tag_weights
    }

    file_exists = os.path.isfile(log_file) and os.path.getsize(log_file) > 0

    with open(log_file, mode='a', encoding='utf-8', newline='') as file:
        fieldnames = ['timestamp', 'all_users', 'participants', 'matching_num', 'tag_weights']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(stats)

    return stats
