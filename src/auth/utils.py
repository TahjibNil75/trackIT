from passlib.context import CryptContext
import jwt
import uuid
import logging
from datetime import datetime, timedelta
from src.config import Config


password_context = CryptContext(schemes=["argon2"], deprecated="auto")

ACCESS_TOKEN_EXPIRY=3600  # 1 hour in seconds

def generate_hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)



def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False):
    # Determine the token expiration time
    if expiry is not None:
        # If a custom expiry duration is provided, use it
        expiration_time = datetime.now() + expiry
    else:
        # Otherwise, use the default access token expiry time
        expiration_time = datetime.now() + timedelta(seconds=ACCESS_TOKEN_EXPIRY)

    # Build the token payload
    payload = {
        "user": user_data,          # Include user information in token
        "exp": expiration_time,     # Set token expiration time
        "jti": str(uuid.uuid4()),   # Unique token identifier
        "refresh": refresh          # Indicates if this is a refresh token
    }

    # Encode the payload into a JWT token
    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    return token


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,                         # The JWT token to decode
            key=Config.JWT_SECRET,              # Secret key used to verify the token
            algorithms=[Config.JWT_ALGORITHM]   # Algorithm(s) expected to be used for signing
        )
        return token_data

    except jwt.PyJWKError as e:
        logging.exception(e)
        # Return None to indicate the token could not be decoded
        return None