# client/main.py
import socket
import json
from crypto_utils import CryptoUtils
from constants import *

class FileClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.symmetric_key = None
        self.cipher_type = None
    
    def connect(self):
        self.socket.connect((self.host, self.port))
        print(f"Conectado ao servidor {self.host}:{self.port}")
    
    def register(self, username, password, algorithm='sha256'):
        self._send_data({
            'action': 'register',
            'username': username,
            'password': password,
            'algorithm': algorithm
        })
        return self._receive_data()['status'] == 'success'
    
    def login(self, username, password):
        self._send_data({
            'action': 'login',
            'username': username,
            'password': password
        })
        response = self._receive_data()
        if response['status'] == 'success':
            self.username = username
            return True
        return False
    
    def perform_key_exchange(self, method='DH', cipher_type='AES'):
        self.cipher_type = cipher_type
        
        if method == 'DH':
            # Diffie-Hellman
            private_key = CryptoUtils.generate_dh_parameters()
            public_key = private_key.public_key()
            
            # Envia chave pública para o servidor
            self._send_data({
                'method': 'DH',
                'public_key': public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                'cipher_type': cipher_type
            })
            
            # Recebe chave pública do servidor
            server_public_key = self._receive_data()['public_key']
            peer_public_key = serialization.load_pem_public_key(
                server_public_key.encode(),
                backend=default_backend()
            )
            
            # Calcula chave compartilhada
            shared_key = CryptoUtils.perform_dh_key_exchange(
                private_key,
                peer_public_key
            )
            
            # Deriva chave simétrica
            kdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'handshake data',
                backend=default_backend()
            )
            self.symmetric_key = kdf.derive(shared_key)
            
        elif method == 'PKI':
            # Usando RSA para enviar chave simétrica
            private_key, public_key = CryptoUtils.generate_rsa_key_pair()
            symmetric_key = CryptoUtils.generate_symmetric_key(cipher_type)
            
            # Envia chave simétrica criptografada
            self._send_data({
                'method': 'PKI',
                'public_key': public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                'encrypted_key': CryptoUtils.encrypt_asymmetric(symmetric_key, public_key),
                'cipher_type': cipher_type
            })
            
            self.symmetric_key = symmetric_key
        
        # Confirmação do servidor
        response = self._receive_data()
        return response.get('status') == 'key_exchange_complete'
    
    def upload_file(self, filename):
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        response = self._send_encrypted_data({
            'action': 'upload',
            'filename': filename.split('/')[-1],
            'file_data': file_data.decode('latin1')  # Para garantir que todos os bytes sejam preservados
        })
        
        return response['status'] == 'upload_success'
    
    def download_file(self, filename, save_path=None):
        response = self._send_encrypted_data({
            'action': 'download',
            'filename': filename
        })
        
        if response['status'] == 'success':
            if not save_path:
                save_path = filename
            with open(save_path, 'wb') as f:
                f.write(response['file_data'].encode('latin1'))
            return True
        return False
    
    def list_files(self):
        response = self._send_encrypted_data({
            'action': 'list'
        })
        
        if response['status'] == 'success':
            return response['files']
        return []
    
    def _send_data(self, data):
        json_data = json.dumps(data).encode(ENCODING)
        self.socket.send(f"{len(json_data):<{HEADER_SIZE}}".encode(ENCODING))
        self.socket.send(json_data)
    
    def _receive_data(self):
        raw_length = self.socket.recv(HEADER_SIZE)
        if not raw_length:
            return None
        length = int(raw_length.decode(ENCODING).strip())
        data = self.socket.recv(length)
        return json.loads(data.decode(ENCODING))
    
    def _send_encrypted_data(self, data):
        json_data = json.dumps(data).encode(ENCODING)
        encrypted_data = CryptoUtils.encrypt_symmetric(json_data, self.symmetric_key, self.cipher_type)
        self._send_data({'data': encrypted_data})
        return self._receive_encrypted_data()
    
    def _receive_encrypted_data(self):
        encrypted_data = self._receive_data()['data']
        decrypted_data = CryptoUtils.decrypt_symmetric(encrypted_data, self.symmetric_key, self.cipher_type)
        return json.loads(decrypted_data.decode(ENCODING))
    
    def close(self):
        self.socket.close()

if __name__ == "__main__":
    # Exemplo de uso
    client = FileClient()
    client.connect()
    
    # Autenticação
    username = input("Username: ")
    password = input("Password: ")
    
    if not client.login(username, password):
        print("Login falhou. Criando nova conta...")
        if not client.register(username, password):
            print("Nome de usuário já existe.")
            exit()
        print("Conta criada com sucesso! Por favor, faça login novamente.")
        if not client.login(username, password):
            print("Erro ao fazer login.")
            exit()
    
    # Troca de chaves
    print("Escolha o método de troca de chaves:")
    print("1. Diffie-Hellman")
    print("2. RSA (PKI)")
    method_choice = input("Escolha (1/2): ")
    method = 'DH' if method_choice == '1' else 'PKI'
    
    print("Escolha o algoritmo de criptografia simétrica:")
    print("1. AES (recomendado)")
    print("2. DES")
    print("3. Blowfish")
    cipher_choice = input("Escolha (1/2/3): ")
    cipher_type = SYMMETRIC_CIPHERS[int(cipher_choice)-1]
    
    if not client.perform_key_exchange(method, cipher_type):
        print("Falha na troca de chaves.")
        exit()
    
    # Menu principal
    while True:
        print("\nMenu:")
        print("1. Enviar arquivo")
        print("2. Baixar arquivo")
        print("3. Listar arquivos")
        print("4. Sair")
        
        choice = input("Escolha: ")
        
        if choice == '1':
            filename = input("Caminho do arquivo para enviar: ")
            if client.upload_file(filename):
                print("Arquivo enviado com sucesso!")
            else:
                print("Falha ao enviar arquivo.")
        
        elif choice == '2':
            filename = input("Nome do arquivo para baixar: ")
            save_path = input("Caminho para salvar (deixe em branco para o diretório atual): ")
            if client.download_file(filename, save_path if save_path else None):
                print("Arquivo baixado com sucesso!")
            else:
                print("Falha ao baixar arquivo.")
        
        elif choice == '3':
            files = client.list_files()
            print("\nArquivos disponíveis:")
            for file in files:
                print(f"- {file}")
        
        elif choice == '4':
            break
    
    client.close()