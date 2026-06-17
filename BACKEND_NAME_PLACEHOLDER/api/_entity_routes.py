from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..config import get_logger
from ..crud import Crud
from ..schema import EntityBase, EntityFilter, EntityFull, UserFull
from ..utils._auth import decode_access_token, oauth2_scheme
from jose import JWTError

log = get_logger()


def define_routes(app: FastAPI, crud: Crud) -> None:
    """Defines the routes for the application."""
    log.debug(f"Entities from crud in define entity routes {crud.get_entities()}")

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

    @app.get(path="/entity/", response_model=list[EntityFull])
    async def get_entities(
        search_string: str | None = None, 
        current_user: UserFull = Depends(get_current_admin)
    ) -> list[EntityFull]:
        """Retrieves entities (admin only)."""
        if search_string is not None:
            filter = EntityFilter(name=search_string, id=None)
        else:
            filter = EntityFilter(name=None, id=None)
        return crud.get_entities(filter)

    @app.get(path="/entity/{id}/", response_model=EntityFull)
    async def get_entity(
        id: int,
        current_user: UserFull = Depends(get_current_admin)
    ):
        """Retrieves a single entity (admin only)."""
        filter = EntityFilter(name=None, id=id)
        result = crud.get_entities(filter)
        if len(result) == 1:
            return result[0]
        raise HTTPException(404, f"No entity found for {id}")

    @app.post(path="/entity/", response_model=EntityFull)
    async def post_entity(
        entity: EntityBase,
        current_user: UserFull = Depends(get_current_admin)
    ) -> EntityFull:
        """Creates a new entity (admin only)."""
        return crud.create_entity(entity)

    @app.put(path="/entity/")
    async def put_entity(
        entity: EntityFull,
        current_user: UserFull = Depends(get_current_admin)
    ):
        """Updates an entity (admin only)."""
        try:
            crud.change_entity(entity)
        except AttributeError as e:
            log.error(f"ERROR: {e}")
            raise HTTPException(status_code=404, detail=str(e))

    @app.delete("/entity/{id}/", response_model=None)
    async def delete_entity(
        id: int,
        current_user: UserFull = Depends(get_current_admin)
    ):
        """Deletes an entity (admin only)."""
        """
        Args:
            id (int): The ID of the entity to be deleted.

        Raises:
            HTTPException: If the entity does not exist or an AttributeError occurs.
        """
        try:
            crud.delete_entity(id)
        except AttributeError as e:
            log.error("No such entity {id}!")
            raise HTTPException(404, str(e))

    assert delete_entity
