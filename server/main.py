# server/main.py
import socket
import json
import threading
from crypto_utils import CryptoUtils
from auth import AuthManager
from file_manager import FileManager
from constants import *

class FileServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.auth_manager = AuthManager()
        self.file_manager = FileManager()
        self.clients = {}
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {self.host}:{self.port}")
        
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
    
    def handle_client(self, client_socket, addr):
        print(f"Conexão estabelecida com {addr}")
        username = None
        
        try:
            # Autenticação
            auth_data = self._receive_data(client_socket)
            if auth_data.get('action') == 'register':
                success = self.auth_manager.register_user(
                    auth_data['username'],
                    auth_data['password'],
                    auth_data.get('algorithm', 'sha256')
                )
                response = {'status': 'success' if success else 'username_taken'}
                self._send_data(client_socket, response)
                return
                
            elif auth_data.get('action') == 'login':
                if self.auth_manager.authenticate_user(auth_data['username'], auth_data['password']):
                    username = auth_data['username']
                    response = {'status': 'success'}
                else:
                    response = {'status': 'invalid_credentials'}
                self._send_data(client_socket, response)
                if response['status'] != 'success':
                    return
            
            # Negociação de chaves
            key_exchange_data = self._receive_data(client_socket)
            
            if key_exchange_data['method'] == 'DH':
                # Diffie-Hellman
                private_key = CryptoUtils.generate_dh_parameters()
                public_key = private_key.public_key()
                
                # Serializa chave pública para enviar ao cliente
                peer_public_key = serialization.load_pem_public_key(
                    key_exchange_data['public_key'].encode(),
                    backend=default_backend()
                )
                
                shared_key = CryptoUtils.perform_dh_key_exchange(
                    private_key,
                    peer_public_key
                )
                
                # Deriva uma chave para criptografia
                kdf = HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=None,
                    info=b'handshake data',
                    backend=default_backend()
                )
                symmetric_key = kdf.derive(shared_key)
                
            elif key_exchange_data['method'] == 'PKI':
                # Usando RSA para enviar chave simétrica
                private_key = serialization.load_pem_private_key(
                    key_exchange_data['private_key'].encode(),
                    password=None,
                    backend=default_backend()
                )
                symmetric_key = CryptoUtils.decrypt_asymmetric(
                    key_exchange_data['encrypted_key'],
                    private_key
                )
            
            # Define o tipo de cifra simétrica
            cipher_type = key_exchange_data.get('cipher_type', 'AES')
            
            # Confirmação para o cliente
            self._send_data(client_socket, {'status': 'key_exchange_complete'})
            
            # Loop principal para comandos
            while True:
                data = self._receive_encrypted_data(client_socket, symmetric_key, cipher_type)
                
                if data['action'] == 'upload':
                    file_data = data['file_data']
                    filename = data['filename']
                    self.file_manager.save_file(username, filename, file_data)
                    response = {'status': 'upload_success'}
                    
                elif data['action'] == 'download':
                    filename = data['filename']
                    file_data = self.file_manager.get_file(username, filename)
                    if file_data:
                        response = {'status': 'success', 'file_data': file_data}
                    else:
                        response = {'status': 'file_not_found'}
                        
                elif data['action'] == 'list':
                    files = self.file_manager.list_files(username)
                    response = {'status': 'success', 'files': files}
                    
                else:
                    response = {'status': 'invalid_action'}
                
                self._send_encrypted_data(client_socket, response, symmetric_key, cipher_type)
                
        except Exception as e:
            print(f"Erro com cliente {addr}: {e}")
        finally:
            client_socket.close()
            if username:
                print(f"Conexão encerrada com {username}@{addr}")
            else:
                print(f"Conexão encerrada com {addr}")
    
    def _receive_data(self, client_socket):
        raw_length = client_socket.recv(HEADER_SIZE)
        if not raw_length:
            return None
        length = int(raw_length.decode(ENCODING).strip())
        data = client_socket.recv(length)
        return json.loads(data.decode(ENCODING))
    
    def _send_data(self, client_socket, data):
        json_data = json.dumps(data).encode(ENCODING)
        client_socket.send(f"{len(json_data):<{HEADER_SIZE}}".encode(ENCODING))
        client_socket.send(json_data)
    
    def _receive_encrypted_data(self, client_socket, key, cipher_type):
        encrypted_data = self._receive_data(client_socket)['data']
        decrypted_data = CryptoUtils.decrypt_symmetric(encrypted_data, key, cipher_type)
        return json.loads(decrypted_data.decode(ENCODING))
    
    def _send_encrypted_data(self, client_socket, data, key, cipher_type):
        json_data = json.dumps(data).encode(ENCODING)
        encrypted_data = CryptoUtils.encrypt_symmetric(json_data, key, cipher_type)
        self._send_data(client_socket, {'data': encrypted_data})

if __name__ == "__main__":
    server = FileServer()
    server.start()