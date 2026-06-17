from fastapi import Depends, FastAPI, HTTPException, status
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from jose import JWTError

from ..config import get_logger
from ..crud import Crud
from ..schema import EntityFilter, PersonBase, PersonFilter, PersonFull, UserFull
from ..utils._auth import decode_access_token, oauth2_scheme

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

    @app.post(path="/person/")
    async def post_person(
        person: PersonBase,
        current_user: UserFull = Depends(get_current_admin),
    ) -> PersonFull:
        try:
            return crud.create_person(person)
        except AttributeError as err:
            log.error(str(err))
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))

    @app.post(path="/person/{entity_id}")
    async def post_person_existing_entity(
        entity_id: int,
        person: PersonBase,
        current_user: UserFull = Depends(get_current_admin),
    ) -> PersonFull:
        try:
            entity_filter = EntityFilter(id=entity_id)
            entity = crud.get_entities(entity_filter)
            if len(entity) != 1:
                raise HTTPException(
                    HTTP_404_NOT_FOUND, detail="ENTITY(%d) not found" % entity_id
                )
            new_person = crud.create_person(person, entity[0])
            return new_person
        except AttributeError as error:
            log.error(str(error))
            raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(error))

    @app.get(path="/person/")
    async def get_persons(
        first_name: str | None = None,
        current_user: UserFull = Depends(get_current_admin),
    ):
        return crud.get_persons(PersonFilter(first_name=first_name))

    @app.get(path="/person/{id}")
    async def get_person_by_id(
        id: int,
        current_user: UserFull = Depends(get_current_admin),
    ):
        filter = PersonFilter(id=id)
        result = crud.get_persons(filter)
        if len(result) != 1:
            raise HTTPException(status_code=404, detail=f"No Person with id {id}")
        return result[0]

    @app.put(path="/person/")
    async def put_person(
        person: PersonFull,
        current_user: UserFull = Depends(get_current_admin),
    ):
        try:
            crud.change_person(person)
        except AttributeError as error:
            raise HTTPException(status_code=404, detail=str(error))

    @app.delete(path="/person/{id}/")
    async def delete_person(
        id: int,
        current_user: UserFull = Depends(get_current_admin),
    ):
        try:
            return crud.delete_person(id)
        except AttributeError as error:
            log.error(error)
            return HTTPException(status_code=404, detail=f"No Person with id {id}")
