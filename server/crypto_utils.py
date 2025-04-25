# server/crypto_utils.py
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os, hashlib

class CryptoUtils:
    @staticmethod
    def generate_symmetric_key(cipher_type='AES', key_size=256):
        """Gera chave simétrica para os 3 tipos de cifra"""
        if cipher_type == 'AES':
            return os.urandom(32) if key_size == 256 else os.urandom(16)
        elif cipher_type == 'DES':
            return os.urandom(8)
        elif cipher_type == 'Blowfish':
            return os.urandom(16)
        else:
            raise ValueError("Cipher type not supported")

    @staticmethod
    def encrypt_symmetric(data, key, cipher_type='AES'):
        """Criptografa dados com cifra simétrica"""
        iv = os.urandom(16)
        
        if cipher_type == 'AES':
            cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        elif cipher_type == 'DES':
            cipher = Cipher(algorithms.TripleDES(key), modes.CFB(iv), backend=default_backend())
        elif cipher_type == 'Blowfish':
            cipher = Cipher(algorithms.Blowfish(key), modes.CFB(iv), backend=default_backend())
        else:
            raise ValueError("Cipher type not supported")
        
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.final()
        encrypted = encryptor.update(padded_data) + encryptor.final()
        
        return iv + encrypted

    @staticmethod
    def decrypt_symmetric(encrypted_data, key, cipher_type='AES'):
        """Descriptografa dados com cifra simétrica"""
        iv = encrypted_data[:16]
        data = encrypted_data[16:]
        
        if cipher_type == 'AES':
            cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        elif cipher_type == 'DES':
            cipher = Cipher(algorithms.TripleDES(key), modes.CFB(iv), backend=default_backend())
        elif cipher_type == 'Blowfish':
            cipher = Cipher(algorithms.Blowfish(key), modes.CFB(iv), backend=default_backend())
        else:
            raise ValueError("Cipher type not supported")
        
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(data) + decryptor.final()
        
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted) + unpadder.final()
        
        return unpadded_data

    @staticmethod
    def generate_dh_parameters():
        """Gera parâmetros para Diffie-Hellman"""
        return ec.generate_private_key(ec.SECP384R1(), default_backend())

    @staticmethod
    def perform_dh_key_exchange(private_key, peer_public_key):
        """Realiza troca de chaves Diffie-Hellman"""
        return private_key.exchange(ec.ECDH(), peer_public_key)

    @staticmethod
    def generate_rsa_key_pair():
        """Gera par de chaves RSA para PKI"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def encrypt_asymmetric(data, public_key):
        """Criptografa com chave pública (PKI)"""
        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def decrypt_asymmetric(encrypted_data, private_key):
        """Descriptografa com chave privada (PKI)"""
        return private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def hash_password(password, algorithm='sha256'):
        """Cria hash de senha com salt"""
        salt = os.urandom(16)
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            raise ValueError("Algorithm not supported")
        
        hash_obj.update(salt + password.encode())
        return salt + hash_obj.digest()

    @staticmethod
    def verify_password(stored_hash, password, algorithm='sha256'):
        """Verifica senha contra hash armazenado"""
        salt = stored_hash[:16]
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            raise ValueError("Algorithm not supported")
        
        hash_obj.update(salt + password.encode())
        return stored_hash[16:] == hash_obj.digest()