from fastapi import FastAPI

from ..config import get_logger
from ..crud import Crud
from ._entity_routes import define_routes as define_entity_routes
from ._user_routes import define_routes as define_user_routes
from ._auth_routes import define_routes as define_auth_routes
from .person_routes import define_routes as define_person_routes

log = get_logger()


def define_routes(app: FastAPI, crud: Crud) -> None:
    """Defines the routes for the application."""
    log.debug(f"Crud entities from define_routes: {crud.get_entities()}")

    @app.get("/")
    async def get_root():
        """
        This function returns an empty dictionary, representing the root of the API.

        Returns:
            A dictionary with one key "/" and value "api_root".

        Example:
            >>> await get_root()
            {'/': 'api_root'}
        """
        return {"": {"/": "api_root"}}

    assert get_root

    define_entity_routes(app, crud)
    define_user_routes(app, crud)
    define_auth_routes(app, crud)
    define_person_routes(app, crud)
