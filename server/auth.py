# server/auth.py
import sqlite3
from crypto_utils import CryptoUtils

class AuthManager:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash BLOB,
                algorithm TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def register_user(self, username, password, algorithm='sha256'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verifica se usuário já existe
        cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return False
        
        # Cria hash da senha
        password_hash = CryptoUtils.hash_password(password, algorithm)
        
        # Armazena usuário
        cursor.execute('''
            INSERT INTO users (username, password_hash, algorithm)
            VALUES (?, ?, ?)
        ''', (username, password_hash, algorithm))
        
        conn.commit()
        conn.close()
        return True

    def authenticate_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT password_hash, algorithm FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
            
        stored_hash, algorithm = result
        return CryptoUtils.verify_password(stored_hash, password, algorithm)