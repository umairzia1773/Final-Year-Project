v# import secrets
# print(secrets.token_hex(32))  # Generates a secure 64-character hex string
# import bcrypt

# stored_hash = b"$2b$12$NxljIUSNdlSrA9eGktK7IuVC/UmXABGh6.7PAV.YJazbXB95KvypG"
# password = "asdf".encode('utf-8')

# if bcrypt.checkpw(password, stored_hash):
#     print("✅ Password matches!")
# else:
#     print("❌ Password does NOT match!")

import requests
response = requests.post("http://127.0.0.1:5000/ask", json={"question": "hello"})
print(response.json())




