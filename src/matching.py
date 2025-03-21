import pandas as pd
import os
from processing_functions import sent_messages
import statistic_functions

def read_users(file_path='all_users.csv', blacklist_path='black_list.csv'):
    """Чтение файла с пользователями, исключая тех, кто в черном списке."""
    try:
        users = pd.read_csv(file_path)
        users = users.dropna(subset=['sex'])
        users['tags'] = users['tags'].apply(eval)

        try:
            with open(blacklist_path, 'r', encoding='utf-8') as f:
                blacklisted_ids = {int(line.strip()) for line in f if line.strip().isdigit()}
        except FileNotFoundError:
            blacklisted_ids = set()

        users = users[~users['chat_id'].isin(blacklisted_ids)]

        return users

    except FileNotFoundError:
        return pd.DataFrame()


def calculate_tag_weights(users):
    """Вычисление весов тегов на основе популярности."""
    tag_counts = {}
    for tags in users['tags']:
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    max_count = max(tag_counts.values())
    tag_weights = {tag: max_count / count for tag, count in tag_counts.items()}
    return tag_weights


def calculate_similarity(user1_id, user2_id, users_df, tag_weights):
    user1 = users_df.loc[users_df['chat_id'] == user1_id].iloc[0]
    user2 = users_df.loc[users_df['chat_id'] == user2_id].iloc[0]
    common_tags = set(user1['tags']).intersection(set(user2['tags']))
    tag_similarity = sum(tag_weights.get(tag, 1) for tag in common_tags)
    age_diff = abs(user1['age'] - user2['age'])
    age_similarity = max(0, 1 - age_diff / 10)
    sex_match = 4 if user1['pair_sex'] == user2['sex'] else 0
    similarity = tag_similarity + age_similarity + sex_match
    return similarity


def find_best_partner(user_id, user_ids, used_pairs, users_df, tag_weights):
    best_score = float('-inf')
    best_partner = None

    for candidate_id in user_ids:
        if candidate_id != user_id and tuple(sorted([int(user_id), int(candidate_id)])) not in used_pairs:
            score = calculate_similarity(user_id, candidate_id, users_df, tag_weights)
            if score > best_score:
                best_score = score
                best_partner = candidate_id

    return best_partner, best_score


def perform_matching(participants_file='participants.csv', users_file='all_users.csv', output_file='matches.csv'):
    participants = pd.read_csv(participants_file)
    users = read_users(users_file)

    if participants.empty or users.empty:
        return

    users = users[users['chat_id'].isin(participants['chat_id'])]
    tag_weights = calculate_tag_weights(users)
    current_matching_num = 1

    if os.path.exists(output_file):
        existing_data = pd.read_csv(output_file)
        used_pairs = set(
            tuple(sorted([(row['User 1']), (row['User 2'])])) for index, row in existing_data.iterrows())
        current_matching_num = existing_data['matching_num'].max() + 1
        print('current_matching_num', current_matching_num)
    else:
        existing_data = pd.DataFrame(columns=['User 1', 'User 2', 'Similarity', 'matching_num'])
        used_pairs = set()

    user_ids = list(users['chat_id'])
    matches = []

    while len(user_ids) > 1:
        user1 = user_ids.pop(0)
        best_partner, similarity = find_best_partner(user1, user_ids, used_pairs, users, tag_weights)
        if best_partner:
            new_pair = tuple(sorted([user1, best_partner]))
            matches.append({'User 1': user1, 'User 2': best_partner, 'Similarity': similarity,
                            'matching_num': current_matching_num})
            used_pairs.add(new_pair)
            user_ids.remove(best_partner)

    if len(user_ids) == 1:
        remaining_user = user_ids[0]
        for user2 in users['chat_id']:
            if user2 != remaining_user and tuple(sorted([remaining_user, user2])) not in used_pairs:
                similarity = calculate_similarity(remaining_user, user2, users, tag_weights)
                matches.append({'User 1': min(remaining_user, user2), 'User 2': max(remaining_user, user2),
                                'Similarity': similarity, 'matching_num': current_matching_num})
                break

    match_df = pd.DataFrame(matches)

    if not match_df.empty:
        print(match_df)
        complete_data = pd.concat([existing_data, match_df], ignore_index=True)
        complete_data.drop_duplicates(subset=['User 1', 'User 2'], keep='first', inplace=True)
        complete_data.to_csv(output_file, index=False)
        sent_messages(match_df)
        statistic_functions.matching_log(matching_num=current_matching_num, tag_weights=tag_weights)
        return tag_weights, current_matching_num

