import json
from utils.secrets import encode, decode


data = {
    "username": "ali",
    "password": "123",
}

print(encode(json.dumps(data)))

encoded = "fUYIXNMSOmM0MiQzLyAsJGN7YWMgLSgyKSQzYzw=NNeQrEPw"

print(decode(encoded))
