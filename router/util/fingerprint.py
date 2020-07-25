from ..flask import *
import hashlib

def getBrowserFingerprint() -> str:
    return hashlib.md5(request.headers.get('User-Agent').encode()).hexdigest()