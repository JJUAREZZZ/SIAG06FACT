# controladores/cifradohelper.py
# funciones para cifrar y descifrar usando derivacion pbkdf2 y sha256 counter mode

import hashlib
import os

def cifrar_datos(data: bytes, password: str) -> bytes:
    # generar sal aleatoria de dieciseis bytes
    salt = os.urandom(16)
    # derivar clave de treinta y dos bytes con pbkdf2
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
    
    # generar flujo de cifrado
    out = bytearray(data)
    block_count = 0
    for i in range(0, len(data), 32):
        keystream = hashlib.sha256(key + salt + block_count.to_bytes(4, 'big')).digest()
        chunk_len = min(32, len(data) - i)
        for j in range(chunk_len):
            out[i + j] ^= keystream[j]
        block_count += 1
    # retornar la sal concatenada con los datos cifrados
    return salt + out

def descifrar_datos(encrypted_data: bytes, password: str) -> bytes:
    if len(encrypted_data) < 16:
        raise ValueError("datos cifrados muy cortos o invalidos")
    salt = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
    
    out = bytearray(ciphertext)
    block_count = 0
    for i in range(0, len(ciphertext), 32):
        keystream = hashlib.sha256(key + salt + block_count.to_bytes(4, 'big')).digest()
        chunk_len = min(32, len(ciphertext) - i)
        for j in range(chunk_len):
            out[i + j] ^= keystream[j]
        block_count += 1
    return bytes(out)
