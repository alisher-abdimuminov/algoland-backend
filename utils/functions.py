import re


def check_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def check_username(username: str) -> bool:
    if len(username) < 4 or len(username) > 32:
        return False
    
    if not username.isalnum():
        return False
    
    if not any(c.isalpha() for c in username):
        return False
    
    return True
