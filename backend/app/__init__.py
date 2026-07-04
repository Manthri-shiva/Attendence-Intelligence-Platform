# app package initialization

# Global monkey patch to resolve compatibility issues between Passlib and newer Bcrypt versions (e.g. 4.1.0+ / 5.0.0+)
# This prevents:
# 1. "AttributeError: module 'bcrypt' has no attribute '__about__'"
# 2. "ValueError: password cannot be longer than 72 bytes" (thrown by passlib's internal test checks)
try:
    import bcrypt
    
    # 1. Patch AttributeError: module 'bcrypt' has no attribute '__about__'
    if not hasattr(bcrypt, "__about__"):
        class DummyAbout:
            __version__ = getattr(bcrypt, "__version__", "4.0.0")
        bcrypt.__about__ = DummyAbout()
        
    # 2. Patch ValueError: password cannot be longer than 72 bytes
    _original_hashpw = bcrypt.hashpw
    def patched_hashpw(password, salt):
        if isinstance(password, bytes):
            if len(password) > 72:
                password = password[:72]
        elif isinstance(password, str):
            encoded = password.encode('utf-8')
            if len(encoded) > 72:
                password = encoded[:72]
        return _original_hashpw(password, salt)
    bcrypt.hashpw = patched_hashpw

    _original_checkpw = bcrypt.checkpw
    def patched_checkpw(password, hashed_password):
        if isinstance(password, bytes):
            if len(password) > 72:
                password = password[:72]
        elif isinstance(password, str):
            encoded = password.encode('utf-8')
            if len(encoded) > 72:
                password = encoded[:72]
        return _original_checkpw(password, hashed_password)
    bcrypt.checkpw = patched_checkpw

except ImportError:
    pass
