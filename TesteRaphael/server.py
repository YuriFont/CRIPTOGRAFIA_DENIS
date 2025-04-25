import socket
import threading
import json
import queue
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import time
from typing import Dict, List, Tuple

class ChatServer:
    def __init__(self, host: str = 'localhost', port: int = 5000, num_threads: int = 10):
        self.host = host
        self.port = port
        self.num_threads = num_threads
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[socket.socket, dict] = {}
        self.clients_lock = threading.Lock()
        self.thread_pool = []
        self.task_queue = queue.Queue()
        self.running = True
        
        # Gerar par de chaves do servidor
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
    def start(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {self.host}:{self.port}")
        print(f"Pool de threads: {self.num_threads}")
        
        # Iniciar pool de threads
        for i in range(self.num_threads):
            thread = threading.Thread(target=self.worker_thread, args=(i,))
            thread.daemon = True
            thread.start()
            self.thread_pool.append(thread)
            
        # Thread principal para aceitar conexões
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Nova conexão de {address}")
                self.task_queue.put(("new_connection", client_socket))
            except Exception as e:
                print(f"Erro ao aceitar conexão: {e}")
                
    def worker_thread(self, worker_id):
        print(f"Worker thread {worker_id} iniciada")
        while self.running:
            try:
                task_type, data = self.task_queue.get(timeout=0.5)
                
                if task_type == "new_connection":
                    self.handle_new_connection(data)
                elif task_type == "message":
                    client_socket, encrypted_message = data
                    self.process_message(client_socket, encrypted_message)
                
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erro na worker thread {worker_id}: {e}")
            
    def handle_new_connection(self, client_socket: socket.socket):
        try:
            # Enviar chave pública para o cliente
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            client_socket.send(public_pem)
            
            # Receber chave secreta criptografada
            encrypted_secret_key = client_socket.recv(2048)
            secret_key = self.private_key.decrypt(
                encrypted_secret_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Receber nome do usuário criptografado
            encrypted_username = client_socket.recv(1024)
            cipher = Cipher(algorithms.AES(secret_key), modes.CFB(b'\0' * 16))
            decryptor = cipher.decryptor()
            username = decryptor.update(encrypted_username) + decryptor.finalize()
            username = username.decode('utf-8')
            
            # Armazenar informações do cliente
            with self.clients_lock:
                self.clients[client_socket] = {
                    'username': username,
                    'secret_key': secret_key
                }
            
            # Iniciar thread para receber mensagens do cliente
            client_thread = threading.Thread(target=self.handle_client_messages, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
            
            # Enviar mensagem de conexão para todos
            self.broadcast_message(f"{username} conectado", None)
            print(f"Usuário {username} conectado")
            
        except Exception as e:
            print(f"Erro ao processar nova conexão: {e}")
            client_socket.close()
            
    def handle_client_messages(self, client_socket: socket.socket):
        while self.running:
            try:
                # Receber mensagem criptografada
                encrypted_message = client_socket.recv(4096)
                if not encrypted_message:
                    break
                
                # Enviar para a fila de tarefas para processamento
                self.task_queue.put(("message", (client_socket, encrypted_message)))
                
            except Exception as e:
                print(f"Erro ao receber mensagem do cliente: {e}")
                break
                
        self.remove_client(client_socket)
    
    def process_message(self, client_socket: socket.socket, encrypted_message: bytes):
        try:
            # Verificar se o cliente ainda está conectado
            with self.clients_lock:
                if client_socket not in self.clients:
                    return
                
                client_info = self.clients[client_socket]
            
            # Decriptografar mensagem
            cipher = Cipher(algorithms.AES(client_info['secret_key']), modes.CFB(b'\0' * 16))
            decryptor = cipher.decryptor()
            message = decryptor.update(encrypted_message) + decryptor.finalize()
            message = message.decode('utf-8')
            
            # Broadcast da mensagem
            formatted_message = f"({client_info['username']}): {message}"
            self.broadcast_message(formatted_message, client_socket)
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
        
    def broadcast_message(self, message: str, sender_socket: socket.socket = None):
        with self.clients_lock:
            clients_copy = self.clients.copy()
            
        for client_socket, client_info in clients_copy.items():
            if client_socket != sender_socket:
                try:
                    # Criptografar mensagem com a chave do cliente
                    cipher = Cipher(algorithms.AES(client_info['secret_key']), modes.CFB(b'\0' * 16))
                    encryptor = cipher.encryptor()
                    encrypted_message = encryptor.update(message.encode()) + encryptor.finalize()
                    client_socket.send(encrypted_message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {client_info['username']}: {e}")
                    
    def remove_client(self, client_socket: socket.socket):
        with self.clients_lock:
            if client_socket in self.clients:
                username = self.clients[client_socket]['username']
                del self.clients[client_socket]
                client_socket.close()
                
        self.broadcast_message(f"{username} desconectado", None)
        print(f"Usuário {username} desconectado")
            
    def stop(self):
        self.running = False
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                self.remove_client(client_socket)
        self.server_socket.close()
        print("Servidor encerrado")

if __name__ == "__main__":
    import sys
    
    try:
        num_threads = 10
        if len(sys.argv) > 1:
            num_threads = int(sys.argv[1])
            
        server = ChatServer(num_threads=num_threads)
        print(f"Iniciando servidor com {num_threads} threads...")
        server.start()
        
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        if 'server' in locals():
            server.stop()
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}") 