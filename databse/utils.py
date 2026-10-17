import socket

import secrets
import string

def check_tcp(host: str, port: int, timeout: int = 30) -> bool:
    if not host or not port:
        return False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        rc = sock.connect_ex((host, port))
        if rc == 0:
            return  True
        return False
    except:
        return False


def generate_password(length: int = 24) -> str:
    """生成满足复杂度要求的随机密码。"""
    _LOWER = string.ascii_lowercase
    _UPPER = string.ascii_uppercase
    _DIGITS = string.digits
    _SPECIAL = "!@#$%^&*()-_=+"
    _ALL = _LOWER + _UPPER + _DIGITS + _SPECIAL
    if length < 12:
        raise ValueError("密码长度至少 12 位")
    while True:
        pwd = "".join(secrets.choice(_ALL) for _ in range(length))
        if (any(c in _LOWER for c in pwd)
                and any(c in _UPPER for c in pwd)
                and any(c in _DIGITS for c in pwd)
                and any(c in _SPECIAL for c in pwd)):
            return pwd