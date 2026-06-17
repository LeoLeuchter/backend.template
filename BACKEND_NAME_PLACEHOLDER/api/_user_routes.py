from fastapi import Depends, FastAPI, HTTPException, status
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from jose import JWTError

from ..config import get_logger
from ..crud import Crud
from ..schema import EntityFilter, UserBase, UserFilter, UserFull
from ..utils._auth import get_password_hash, decode_access_token, oauth2_scheme

log = get_logger()


def define_routes(app: FastAPI, crud: Crud) -> None:

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
        except JWTError:
            raise credentials_exception

        user = crud.get_user_by_username(username)
        if user is None or not user.is_admin:
            raise credentials_exception

        return UserFull(
            id=user.entity_id,
            user_name=user.user_name,
            name=user.entity.name,
            password_hash=user.password_hash,
            is_admin=user.is_admin,
        )

    @app.post(path="/user/")
    async def post_user(
        user: UserBase,
        current_user: UserFull = Depends(get_current_admin),
    ) -> UserFull:
        try:
            hashed_password = get_password_hash(user.password_hash)
            secure_user = UserBase(
                user_name=user.user_name,
                name=user.name,
                password_hash=hashed_password,
                is_admin=user.is_admin,
            )
            return crud.create_user(secure_user)
        except AttributeError as err:
            log.error(str(err))
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))

    @app.post(path="/user/{entity_id}")
    async def post_user_existing_entity(
        entity_id: int,
        user: UserBase,
        current_user: UserFull = Depends(get_current_admin),
    ) -> UserFull:
        try:
            entity_filter = EntityFilter(id=entity_id)
            entity = crud.get_entities(entity_filter)
            if len(entity) != 1:
                raise HTTPException(
                    HTTP_404_NOT_FOUND, detail="ENTITY(%d) not found" % entity_id
                )
            hashed_password = get_password_hash(user.password_hash)
            secure_user = UserBase(
                user_name=user.user_name,
                name=user.name,
                password_hash=hashed_password,
                is_admin=user.is_admin,
            )
            new_user = crud.create_user(secure_user, entity[0])
            return new_user
        except AttributeError as error:
            log.error(dir(error))
            log.error(error)
            raise HTTPException(status_code=HTTP_409_CONFLICT, detail=error)

    @app.get(path="/user/")
    async def get_user(
        filter: str | None = None,
        current_user: UserFull = Depends(get_current_admin),
    ):
        return crud.get_users(UserFilter(name=filter))

    @app.get(path="/user/{id}")
    async def get_user_by_id(
        id: int,
        current_user: UserFull = Depends(get_current_admin),
    ):
        filter = UserFilter(id=id)
        result = crud.get_users(filter)
        if len(result) != 1:
            raise HTTPException(status_code=404, detail=f"No User with id {id}")
        return result[0]

    @app.put(path="/user/")
    async def _put_user(
        user: UserFull,
        current_user: UserFull = Depends(get_current_admin),
    ):
        try:
            crud.change_user(user)
        except AttributeError as error:
            raise HTTPException(status_code=404, detail=str(error))

    @app.delete(path="/user/{id}/")
    async def _delete_user(
        id: int,
        current_user: UserFull = Depends(get_current_admin),
    ):
        try:
            return crud.delete_user(id)
        except AttributeError as error:
            log.error(error)
            return HTTPException(status_code=404, detail=f"No User with id {id}")
