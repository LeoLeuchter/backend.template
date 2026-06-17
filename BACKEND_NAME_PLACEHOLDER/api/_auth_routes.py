from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

from ..schema import Token, TokenData, UserFull
from ..utils._auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    oauth2_scheme,
    verify_password,
)


async def get_current_admin_user(token: str = Depends(oauth2_scheme)) -> UserFull:
    """Validate token and ensure user is admin."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated or not an admin",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = None
    crud = None  # Will be passed via context
    # User will be fetched in the route itself
    return token_data  # type: ignore


def define_routes(app: FastAPI, crud) -> None:
    @app.post(path="/token", response_model=Token)
    async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
    ) -> Token:
        user = crud.get_user_by_username(form_data.username)
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user.user_name})
        return Token(access_token=access_token, token_type="bearer")

    async def get_current_admin(token: str = Depends(oauth2_scheme)) -> UserFull:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or not an admin",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = decode_access_token(token)
            username: str | None = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception

        user = crud.get_user_by_username(token_data.username)
        if user is None or not user.is_admin:
            raise credentials_exception

        return UserFull(
            id=user.entity_id,
            user_name=user.user_name,
            name=user.entity.name,
            password_hash=user.password_hash,
            is_admin=user.is_admin,
        )

    @app.get(path="/users/me", response_model=UserFull)
    async def read_current_user(
        current_user: UserFull = Depends(get_current_admin),
    ) -> UserFull:
        return current_user
