from src.auth.service import UserService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException
from fastapi import status, Depends, Request
from .utils import decode_token
from sqlmodel.ext.asyncio.session import AsyncSession 
from src.db.main import get_session

user_service = UserService()


class TokenBearer(HTTPBearer):
    """Base class for JWT token authentication."""

    async def __call__(self, request: Request) -> dict:
        creds = await super().__call__(request)     # Call parent HTTPBearer to extract credentials from Authorization header
        token = creds.credentials                   # Extract the JWT token string from the credentials object
        token_data = decode_token(token)            # Decode the JWT token into a dictionary
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # # Check if the token's JTI (JWT ID) is in the blocklist
        # if await token_in_blocklist(token_data["jti"]):
        #     # Raise 403 Forbidden error for blocklisted tokens
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail={
        #             "error": "This token is invalid or expired",
        #             "resolution": "Please get new token or login again"
        #         }
        #     )

        self.verify_token_data(token_data)      # Call child class method to verify token type (access vs refresh)
        return token_data                       # Return the decoded token data for use in route handlers



        # Let child classes verify token type
    def verify_token_data(self, token_data: dict) -> dict:
        """Child classes should implement this method to verify specific token types."""
        raise NotImplementedError("Subclasses must implement verify_token_data method.")
    
class AccessTokenBearer(TokenBearer):
    """Only accepts access tokens (refresh=False)"""
    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get('refresh'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token required.",
            )
        
class RefreshTokenBearer(TokenBearer):
    """Only accepts refresh tokens (refresh=True)"""
    def verify_token_data(self, token_data: dict) -> None:
        if not token_data.get('refresh'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required.",
            )


async def get_current_user(
        token_details: dict = Depends(AccessTokenBearer()),
        session: AsyncSession = Depends(get_session)
):
    user_email = token_details["user"]["email"]
    user = await user_service.get_user_by_email(user_email, session)
    return user

