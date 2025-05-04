import base64
import random
import string
import json

def generate_random_slice(length: int) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def encode(text: str, key: str = "A", slice_length: int = 8) -> str:
    text_bytes = text.encode('utf-8')
    key_bytes = key.encode('utf-8')
    
    encoded_bytes = bytes(text_byte ^ key_bytes[i % len(key_bytes)] for i, text_byte in enumerate(text_bytes))
    encoded_str = base64.b64encode(encoded_bytes).decode('utf-8')
    
    random_start = generate_random_slice(slice_length)
    random_end = generate_random_slice(slice_length)
    
    return random_start + encoded_str + random_end

def decode(encoded_text: str, key: str = "A", slice_length: int = 8) -> str:
    sliced_str = encoded_text[slice_length:-slice_length]
    decoded_bytes = base64.b64decode(sliced_str)
    key_bytes = key.encode('utf-8')
    
    decoded_text_bytes = bytes(decoded_byte ^ key_bytes[i % len(key_bytes)] for i, decoded_byte in enumerate(decoded_bytes))
    
    return decoded_text_bytes.decode('utf-8')

def jsonify(data: str):
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {}
