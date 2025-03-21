from sqlalchemy import Column, Integer, String, MetaData, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Participant(Base):
    __tablename__ = 'participants'
    chat_id = Column(String, primary_key=True, unique=True, nullable=False)  # Уникальный идентификатор

class AllUsers(Base):
    __tablename__ = 'all_users'
    chat_id = Column(Integer, primary_key=True, unique=True,
                     nullable=False)
    user_id = Column(Integer, unique=True, nullable=False)  # Идентификатор пользователя
    name = Column(String, nullable=False)  # Имя пользователя
    age = Column(Integer, nullable=False)  # Возраст
    sex = Column(String, nullable=False)  # Пол
    pair_sex = Column(String, nullable=False)  # Предпочитаемый пол для пары
    specialization = Column(String, nullable=False)  # Специализация
    username = Column(String, nullable=True)  # Юзернейм
    tags = Column(String, nullable=True)  # Теги

class Matches(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_1 = Column(String, ForeignKey('all_users.chat_id'), nullable=False)  # Пользователь 1 (ссылка на all_users)
    user_2 = Column(String, ForeignKey('all_users.chat_id'), nullable=False)  # Пользователь 2 (ссылка на all_users)
    similarity = Column(Float, nullable=False)  # Сходство (от 0 до 1)
    matching_num = Column(Integer, nullable=False)  # Номер совпадения

class MatchingRate(Base):
    __tablename__ = 'matching_rate'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_1 = Column(String, ForeignKey('all_users.chat_id'), nullable=False)  # Пользователь 1
    user_2 = Column(String, ForeignKey('all_users.chat_id'), nullable=False)  # Пользователь 2
    matching_num = Column(Integer, nullable=False)  # Номер совпадения
    rating_from_user_1 = Column(String, nullable=False)  # Рейтинг в формате JSON