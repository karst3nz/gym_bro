import sqlite3
from aiogram import types
import os
from utils.log import create_logger

logger = create_logger(__name__)



class DB:

    users_table = "users"

    def __init__(self):
        from config import db_DIR, bot
        if not os.path.isdir(db_DIR):
            os.mkdir(db_DIR)
        self.conn = sqlite3.connect(db_DIR + "db.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.run()
        
       
    def run(self):
        """
        Создание таблиц БД
        """
        # Создание основной таблицы с пользователями
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id                      INTEGER PRIMARY KEY,
                user_id                 INTEGER NOT NULL,
                tg_username             TEXT,
                tg_firstname            TEXT       
            )
        ''')
        # Таблица для веса пользователя
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS weights (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                weight REAL NOT NULL,
                date INTEGER NOT NULL
            )
        ''')
        # Таблица для рабочих сетов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS worksets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                exercise TEXT NOT NULL,
                weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                date INTEGER NOT NULL
            )
        ''')
        # Таблица для рекордов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                exercise TEXT NOT NULL,
                weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                date INTEGER NOT NULL
            )
        ''')
        self.conn.commit()
    
    def insert(self, user_id: int, tg_username: str, tg_firstname: str):
        """
        Вставка пользователя в основную БД после подтверждения
        """
        is_user = self.get(user_id=user_id, data="user_id", table=DB.users_table)
        if is_user is None:
            self.cursor.execute(
                'INSERT INTO users (user_id, tg_username, tg_firstname) '
                'VALUES (?, ?, ?)',
                (user_id, tg_username, tg_firstname))
            self.conn.commit()
        else:
            pass


    def get(self, user_id: int, data: str, table: str):
        """
        Получние данных из БД по user_id
        """
        
        self.cursor.execute(
            f"SELECT {data} FROM {table} WHERE user_id = ?",
            (user_id, ))
        
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None
    
    def get_without_user_id(self, data: str, table: str):
        """
        Получние данных из БД без user_id
        """
        
        self.cursor.execute(f"SELECT {data} FROM {table}")
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None
        
    
    def get_all_user_id(self, user_id: int, data: str, table: str):
        """
        Получение всех данных из БД по user_id и data 
        """
        
        self.cursor.execute(f"SELECT {data} FROM {table} WHERE user_id = ?", (user_id, ))
        fetch = self.cursor.fetchall()
        result = []
        for item in fetch:
            item = item[0]
            result.append(item)
        return result
    
    def get_all(self, data: str, table: str):
        """
        Получение всех данных из БД по data
        """
        self.cursor.execute(f"SELECT {data} FROM {table}")
        fetch = self.cursor.fetchall()
        result = []
        for item in fetch:
            item = item[0]
            result.append(item)
        return result

    def delete(self, user_id: int, table: str):
        """
        Удаление строчки из БД
        """
        
        try:
            self.cursor.execute(f"DELETE from {table} where user_id = ?", (user_id,))
            self.conn.commit()
            return True
        except Exception:
            return False

    def update(self, user_id: int, column: str, new_data: str, table: str):
        """
        Обновление данных в БД
        """
        
        try:
            self.cursor.execute(f"UPDATE {table} SET {column} = ? WHERE user_id = ?", (new_data, user_id))
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def update_without_user_id(self, column: str, new_data: str, table: str):
        """
        Обновление данных в БД
        """
        
        try:
            self.cursor.execute(f"UPDATE {table} SET {column} = ?", (new_data, ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(e)

    
