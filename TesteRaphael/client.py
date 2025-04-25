import socket
import threading
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import time

class ChatClient:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.secret_key = os.urandom(32)  # Chave AES-256
        self.message_buffer = []
        
    def connect(self, username: str):
        try:
            self.socket.connect((self.host, self.port))
            
            # Receber chave pública do servidor
            server_public_key_pem = self.socket.recv(2048)
            server_public_key = serialization.load_pem_public_key(
                server_public_key_pem,
                backend=default_backend()
            )
            
            # Enviar chave secreta criptografada
            encrypted_secret_key = server_public_key.encrypt(
                self.secret_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            self.socket.send(encrypted_secret_key)
            
            # Enviar nome de usuário criptografado
            cipher = Cipher(algorithms.AES(self.secret_key), modes.CFB(b'\0' * 16))
            encryptor = cipher.encryptor()
            encrypted_username = encryptor.update(username.encode()) + encryptor.finalize()
            self.socket.send(encrypted_username)
            
            self.running = True
            
            # Iniciar thread para receber mensagens
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False
            
    def send_message(self, message: str):
        try:
            # Criptografar mensagem
            cipher = Cipher(algorithms.AES(self.secret_key), modes.CFB(b'\0' * 16))
            encryptor = cipher.encryptor()
            encrypted_message = encryptor.update(message.encode()) + encryptor.finalize()
            self.socket.send(encrypted_message)
            
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            
    def receive_messages(self):
        while self.running:
            try:
                # Receber mensagem criptografada
                encrypted_message = self.socket.recv(4096)
                if not encrypted_message:
                    break
                    
                # Decriptografar mensagem
                cipher = Cipher(algorithms.AES(self.secret_key), modes.CFB(b'\0' * 16))
                decryptor = cipher.decryptor()
                message = decryptor.update(encrypted_message) + decryptor.finalize()
                decoded_message = message.decode('utf-8')
                print(f"\n{decoded_message}")
                print("Digite uma mensagem: ", end='', flush=True)
                
            except Exception as e:
                print(f"\nErro ao receber mensagem: {e}")
                break
                
        self.running = False
        
    def disconnect(self):
        self.running = False
        self.socket.close()

def main():
    client = ChatClient()
    username = input("Digite seu nome de usuário: ")
    
    if client.connect(username):
        print("Conectado ao servidor!")
        
        try:
            while True:
                message = input("Digite uma mensagem: ")
                if message.lower() == 'sair':
                    break
                client.send_message(message)
        except KeyboardInterrupt:
            pass
            
        client.disconnect()

if __name__ == "__main__":
    main() 