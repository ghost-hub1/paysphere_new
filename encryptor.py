# === encrypt_site.py with chunking & Render URL logging ===
import os, json, base64, zipfile, math
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from datetime import datetime, timedelta

SITE_DIR = "site"
OUTPUT_FILE = "payload_core.b64"
TOKEN_DB = "tokens.json"
URL_LOG = "url.txt"
RENDER_DOMAIN = "https://paysphere.42web.io"  # <<< CHANGE THIS!

def zip_directory(directory):
    zip_path = "site.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, directory)
                zipf.write(filepath, arcname)
    return zip_path

def encrypt_file(input_file, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    with open(input_file, 'rb') as f:
        data = f.read()
    padding_len = AES.block_size - len(data) % AES.block_size
    data += bytes([padding_len]) * padding_len
    encrypted = cipher.encrypt(data)
    return base64.b64encode(encrypted).decode()

def generate_token():
    return base64.urlsafe_b64encode(os.urandom(12)).decode().rstrip("=")

def save_token(token, key, iv):
    if os.path.exists(TOKEN_DB):
        with open(TOKEN_DB) as f:
            tokens = json.load(f)
    else:
        tokens = {}
    tokens[token] = {
        "key": base64.b64encode(key).decode(),
        "iv": base64.b64encode(iv).decode(),
        "created": datetime.utcnow().isoformat(),
        "expires": (datetime.utcnow() + timedelta(weeks=8)).isoformat(),
        "status": "active"
    }
    with open(TOKEN_DB, 'w') as f:
        json.dump(tokens, f, indent=2)

    access_url = f"{RENDER_DOMAIN}/gateway.php?t={token}"
    with open(URL_LOG, "a") as f:
        f.write(access_url + "\n")
    print(f"[+] Access URL: {access_url}")

def split_file(content, parts):
    chunk_size = math.ceil(len(content) / parts)
    for i in range(parts):
        chunk = content[i * chunk_size: (i + 1) * chunk_size]
        with open(f"payload_part_{i+1}.b64", 'w') as f:
            f.write(chunk)
    print(f"[+] Split into {parts} part(s) as payload_part_#.b64")

def main():
    print("[*] Zipping site directory...")
    zip_path = zip_directory(SITE_DIR)

    key = get_random_bytes(32)
    iv = get_random_bytes(16)
    print("[*] Encrypting zip archive...")
    encrypted_b64 = encrypt_file(zip_path, key, iv)

    with open(OUTPUT_FILE, 'w') as f:
        f.write(encrypted_b64)
    print(f"[+] Payload saved to {OUTPUT_FILE}")

    token = generate_token()
    save_token(token, key, iv)
    print(f"[+] Token: {token}")

    # Ask how many parts to split
    try:
        parts = int(input("How many parts do you want to split the payload into? (e.g., 4): ").strip())
        if parts > 1:
            split_file(encrypted_b64, parts)
            os.remove(OUTPUT_FILE)
            print(f"[i] Original payload_core.b64 deleted after splitting.")
        else:
            print("[i] Skipping splitting, keeping payload_core.b64.")
    except Exception as e:
        print(f"[!] Error during splitting: {e}")
        print("[!] Keeping payload_core.b64 as-is.")

if __name__ == "__main__":
    main()
