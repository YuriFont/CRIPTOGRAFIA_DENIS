import socket
import threading
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import time
import sys
import queue

class ChatClient:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.secret_key = os.urandom(32)  # Chave AES-256
        self.message_queue = queue.Queue()
        self.receive_thread = None
        self.lock = threading.Lock()
        self.print_lock = threading.Lock()
        self.message_history = []  # Lista para armazenar o histórico de mensagens
        self.max_history = 10  # Número máximo de mensagens a serem exibidas
        
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
            encrypted_username = encryptor.update(username.encode('utf-8')) + encryptor.finalize()
            self.socket.send(encrypted_username)
            
            self.running = True
            
            # Iniciar thread para receber mensagens
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = False
            self.receive_thread.start()
            
            # Iniciar thread para processar mensagens
            process_thread = threading.Thread(target=self.process_messages)
            process_thread.daemon = False
            process_thread.start()
            
            # Exibir prompt inicial
            self.display_messages()
            
            return True
            
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False
            
    def display_messages(self):
        """Exibe todas as mensagens do histórico"""
        with self.print_lock:
            # Limpar a tela
            print("\033[2J\033[H", end="")
            # Exibir histórico de mensagens
            for msg in self.message_history[-self.max_history:]:
                print(msg)
                
    def send_message(self, message: str):
        try:
            with self.lock:
                if not self.running:
                    return
                    
                # Adicionar mensagem ao histórico
                self.message_history.append(f"(Você): {message}")
                # Exibir todas as mensagens
                self.display_messages()
                    
                # Criptografar mensagem
                cipher = Cipher(algorithms.AES(self.secret_key), modes.CFB(b'\0' * 16))
                encryptor = cipher.encryptor()
                encrypted_message = encryptor.update(message.encode('utf-8')) + encryptor.finalize()
                self.socket.send(encrypted_message)
            
        except Exception as e:
            if self.running:
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
                
                try:
                    decoded_message = message.decode('utf-8')
                    self.message_queue.put(decoded_message)
                except UnicodeDecodeError:
                    # Se não conseguir decodificar como UTF-8, ignora a mensagem
                    continue
                
            except Exception as e:
                if self.running:
                    print(f"\nErro ao receber mensagem: {e}")
                break
                
        self.running = False
        
    def process_messages(self):
        while self.running:
            try:
                message = self.message_queue.get(timeout=0.1)
                # Adicionar mensagem ao histórico
                self.message_history.append(message)
                # Exibir todas as mensagens
                self.display_messages()
            except queue.Empty:
                continue
            except Exception as e:
                if self.running:
                    print(f"\nErro ao processar mensagem: {e}")
                break
                
    def disconnect(self):
        try:
            with self.lock:
                self.running = False
                # Enviar mensagem de desconexão
                self.send_message("sair")
                time.sleep(0.1)  # Pequeno delay para garantir que a mensagem seja enviada
                self.socket.close()
                
            # Aguardar threads terminarem
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=1.0)
                
        except Exception as e:
            print(f"Erro ao desconectar: {e}")

def main():
    client = ChatClient()
    username = input("Digite seu nome de usuário: ")
    
    if client.connect(username):
        print("Conectado ao servidor!")
        # Exibir prompt inicial
        print("Digite uma mensagem: ", end='', flush=True)
        
        try:
            while True:
                message = input()
                if message.lower() == 'sair':
                    client.disconnect()
                    break
                client.send_message(message)
                # Exibir prompt após enviar mensagem
                print("Digite uma mensagem: ", end='', flush=True)
        except KeyboardInterrupt:
            print("\nEncerrando cliente...")
            client.disconnect()
        except Exception as e:
            print(f"Erro: {e}")
            client.disconnect()
        finally:
            sys.exit(0)

if __name__ == "__main__":
    main() 
