import csv
import os
import messages
import pandas as pd

class AdminManager:
    def __init__(self, filename="admins.csv"):
        self.filename = filename
        self.fieldnames = ['username']

    def check_admin(self, username):
        """ Проверяет наличие администратора в файле admins.csv """
        if not os.path.exists(self.filename):
            print("Файл не найден.")
            return False

        if os.path.getsize(self.filename) == 0:
            print("Файл пуст.")
            return False

        with open(self.filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != self.fieldnames:
                print("Неверная структура файла.")
                return False

            for row in reader:
                if row['username'] == username:
                    return True
        return False

    def add_admin(self, username):
        """ Добавляет администратора в admins.csv """
        admin_exists = self.check_admin(username)
        if admin_exists:
            print("Админ уже существует.")
            return False

        write_headers = not os.path.isfile(self.filename) or os.path.getsize(self.filename) == 0

        with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)

            if write_headers:
                writer.writeheader()

            writer.writerow({'username': username})
            print("Админ успешно добавлен.")
            return True

    def remove_admin(self, username):
        """ Удаляет администратора из admins.csv """
        if not os.path.exists(self.filename) or os.path.getsize(self.filename) == 0:
            print("Файл не найден или пуст.")
            return False

        removed = False
        admins = []
        with open(self.filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != self.fieldnames:
                print("Неверная структура файла.")
                return False

            for row in reader:
                if row['username'] == username:
                    removed = True
                    continue
                admins.append(row)

        if removed:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(admins)

        return removed


class UserManager:
    def __init__(self, profiles_file='profiles_updates.csv', blacklist_file='black_list.csv', all_users_file='all_users.csv'):
        self.profiles_file = profiles_file
        self.blacklist_file = blacklist_file
        self.all_users_file = all_users_file

    def get_profiles(self):
        with open(self.profiles_file, 'r', encoding='utf-8') as file:
            return list(csv.reader(file))

    def remove_profile(self, chat_id):
        profiles = self.get_profiles()
        with open(self.profiles_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(row for row in profiles if row[0] != chat_id)

    def add_to_blacklist(self, chat_id):
        with open(self.blacklist_file, 'a', encoding='utf-8', newline='') as file:
            csv.writer(file).writerow([chat_id])

    def remove_from_blacklist(self, chat_id):
        removed = False
        blacklisted = self.get_blacklisted_users()
        if chat_id in blacklisted:
            blacklisted.remove(chat_id)
            removed = True

        with open(self.blacklist_file, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows([[cid] for cid in blacklisted])

        return removed

    def get_blacklisted_users(self):
        if not os.path.exists(self.blacklist_file):
            return []

        with open(self.blacklist_file, 'r', encoding='utf-8') as file:
            return [row[0] for row in csv.reader(file)]

    def get_chat_id_by_username(self, username):
        if not os.path.exists(self.all_users_file):
            return None

        with open(self.all_users_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[1].lstrip('@').lower() == username.lower():
                    return row[0]
        return None

    def updated_profile(self, chat_id):
        """Добавляет пользователя или переносит в начало файла 'profiles_updates.csv'."""
        profiles = self.get_profiles()
        new_profiles = [row for row in profiles if row[0] != chat_id]

        # Вставляет уникального пользователя в начало
        new_profiles.insert(0, [chat_id])

        # Перезаписывает файл с обновленным списком профилей
        with open(self.profiles_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(new_profiles)

class MatchingManager:
    @staticmethod
    def get_matching_info(index):
        possible_questions = [
            'Насколько вас устроил возраст собеседника?',
            'Вы хотели бы чтобы в будущем мы рекомендовали вам',
            'Насколько совпали ли ваши интересы?',
            'Насколько интересен собеседник?'
        ]

        answers = [
            'Людей с похожими интересами',
            'Людей с другими интересами',
            'Случайных людей'
        ]

        matches = pd.read_csv('matches.csv')
        matching_rate = pd.read_csv('matching_rate.csv', names=['user 1', 'user 2', 'matching_num', 'scores'])

        if index >= len(matches) or index < 0:
            return None

        matching = matches.iloc[-(index + 1)]  # начинаем с конца
        matching_num = matching['matching_num']
        matching_score = matching['Similarity']
        user1_id = int(matching['User 1'])
        user2_id = int(matching['User 2'])

        def get_user_ratings(user_from, user_to):
            user_ratings = matching_rate[(matching_rate['user 1'] == user_from) &
                                         (matching_rate['user 2'] == user_to) &
                                         (matching_rate['matching_num'] == matching_num)]
            if user_ratings.empty:
                return {q: None for q in possible_questions}

            scores = eval(user_ratings.iloc[0]['scores'])
            print(scores)
            scores_dict = {}
            for i, q in enumerate(possible_questions):
                if i == 1 and len(scores) > i:
                    score = answers[scores[i] - 1] if scores[i] - 1 < len(answers) else None
                elif i == 3 and len(scores) > i and scores[i] == 6:
                    score = 'не общались'
                else:
                    score = scores[i] if i < len(scores) else None
                scores_dict[q] = score
            print(scores_dict)
            return scores_dict

        info = {
            'matching_num': matching_num,
            'matching_score': matching_score,
            'user1_id': user1_id,
            'user1_profile': messages.user_profile(user1_id, only_stats=True),
            'user1_matching_rate': get_user_ratings(user1_id, user2_id),
            'user2_id': user2_id,
            'user2_profile': messages.user_profile(user2_id, only_stats=True),
            'user2_matching_rate': get_user_ratings(user2_id, user1_id)
        }

        return info

    @staticmethod
    def format_matching_info(info):
        text = f"<b>Матчинг №{int(info['matching_num'])}, similarity: {info['matching_score']}</b>\n\n"
        text += f"<b>Пользователь 1:</b>\n{info['user1_profile']}\n"
        text += "<b>Оценки пользователя 1:</b>\n"
        for q, a in info['user1_matching_rate'].items():
            text += f"{q}: {a}\n"

        text += "\n"
        text += f"<b>Пользователь 2:</b>\n{info['user2_profile']}\n"
        text += "<b>Оценки пользователя 2:</b>\n"
        for q, a in info['user2_matching_rate'].items():
            text += f"{q}: {a}\n"

        return text