import os
import zipfile
import json
import base64
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

# === SETTINGS ===
FOLDER_TO_ZIP = 'site'
ZIP_FILENAME = 'site.zip'
ENCRYPTED_FILENAME = 'payload_core.b64'
TOKENS_FILE = 'tokens.json'
URL_LOG_FILE = 'url.txt'
GATEWAY_URL_BASE = 'https://your-render-app.onrender.com/gateway.php'  # Replace this

# === AUTO CLEAN ZIP AFTER ENCRYPTION? ===
AUTO_DELETE_ZIP = True

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=folder_path)
                zipf.write(full_path, arcname)

def encrypt_file(input_file, output_file, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    with open(output_file, 'wb') as f:
        f.write(base64.b64encode(ciphertext))

def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tokens(tokens):
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)

def log_url(token, url):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(URL_LOG_FILE, 'a') as f:
        f.write(f'[{timestamp}] {token} -> {url}\n')

def generate_token():
    return base64.urlsafe_b64encode(get_random_bytes(12)).decode('utf-8').rstrip('=')

def main():
    print('[*] Zipping site...')
    zip_folder(FOLDER_TO_ZIP, ZIP_FILENAME)

    print('[*] Encrypting...')
    key = get_random_bytes(32)
    iv = get_random_bytes(16)
    encrypt_file(ZIP_FILENAME, ENCRYPTED_FILENAME, key, iv)

    if AUTO_DELETE_ZIP:
        os.remove(ZIP_FILENAME)

    token = generate_token()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    tokens = load_tokens()
    tokens[token] = {
        'key': base64.b64encode(key).decode(),
        'iv': base64.b64encode(iv).decode(),
        'timestamp': timestamp
    }
    save_tokens(tokens)

    access_url = f"{GATEWAY_URL_BASE}?token={token}"
    log_url(token, access_url)

    print('[+] Done!')
    print(f'[+] Access URL: {access_url}')
    print(f'[+] Token: {token}')
    print(f'[+] Key saved to tokens.json with timestamp.')

if __name__ == '__main__':
    main()
