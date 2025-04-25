# server/file_manager.py
import os
import json
from crypto_utils import CryptoUtils

class FileManager:
    def __init__(self, base_dir='server_files'):
        self.base_dir = base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
    
    def get_user_dir(self, username):
        user_dir = os.path.join(self.base_dir, username)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        return user_dir
    
    def save_file(self, username, filename, file_data):
        user_dir = self.get_user_dir(username)
        filepath = os.path.join(user_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_data.encode('latin1'))  # Revertendo a codificação latin1 usada no cliente
    
    def get_file(self, username, filename):
        user_dir = self.get_user_dir(username)
        filepath = os.path.join(user_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return f.read().decode('latin1')  # Codificando em latin1 para preservar todos os bytes
        return None
    
    def list_files(self, username):
        user_dir = self.get_user_dir(username)
        if os.path.exists(user_dir):
            return os.listdir(user_dir)
        return []