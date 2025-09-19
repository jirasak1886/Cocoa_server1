import hashlib, secrets

def gen_otp():
    return f"{secrets.randbelow(10**6):06d}"

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
