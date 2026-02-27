from cryptography.fernet import Fernet

# IMPORTANT: Use the EXACT same secret key as in the main script
SECRET_KEY = b'aVuzD_TMheAHemOnvrBvkh8f4A3--rTBuf8ERiTV0nk='

# Your credentials
BOT_TOKEN = '6143948708:AAFDFjnbEQGUH4gO_93miWUrotF3T2iNIpg'
CHAT_ID = '1701588872'

f = Fernet(SECRET_KEY)
encrypted_bot_token = f.encrypt(BOT_TOKEN.encode('utf-8'))
encrypted_chat_id = f.encrypt(CHAT_ID.encode('utf-8'))

print(f"ENCRYPTED_BOT_TOKEN = {encrypted_bot_token}")
print(f"ENCRYPTED_CHAT_ID = {encrypted_chat_id}")