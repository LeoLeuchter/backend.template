from fastapi import FastAPI

from ..config import get_logger
from ..crud import Crud
from ..engine import get_engine
from ..schema import UserBase
from ..utils._auth import get_password_hash
from ._routes import define_routes

log = get_logger()

_app: FastAPI | None = None
_crud: Crud | None = None


async def startup_event():
    """Create default users if they don't exist."""
    if _crud:
        try:
            # Create test user
            existing_user = _crud.get_user_by_username("testuser")
            if not existing_user:
                test_user = UserBase(
                    user_name="testuser",
                    name="Test User",
                    password_hash=get_password_hash("password123"),
                    is_admin=False,
                )
                _crud.create_user(test_user)
                log.info("Test user created: testuser / password123")
            
            # Create admin user
            existing_admin = _crud.get_user_by_username("admin")
            if not existing_admin:
                admin_user = UserBase(
                    user_name="admin",
                    name="Administrator",
                    password_hash=get_password_hash("Kennwort1"),
                    is_admin=True,
                )
                _crud.create_user(admin_user)
                log.info("Admin user created: admin / Kennwort1")
        except Exception as e:
            log.error(f"Error creating default users: {e}")


"""
Function to build and initialize the application. This function sets up the CRUD object and FastAPI
instance, and defines the routes if they haven't been defined yet. If environment variable
'CONFIG_FILE' is set, it uses that file for configuration.

Returns:
    The initialized FastAPI application instance.
"""
def build_app(crud: Crud | None = None):

    global _crud
    global _app

    if not _crud:
        if crud:
            log.debug(f"Crud Entities in build_app: {crud.get_entities()}")
            _crud = crud
            log.debug("Existing crud provided.")
        else:
            engine = get_engine()
            _crud = Crud(engine)
            log.debug("Creating new crud")

    global _app

    if not _app:
        log.debug("Creating app")
        _app = FastAPI()
        log.debug(f"Provided crud{crud} used crud{_crud}")
        log.debug(f"Crud Entities in build_app with _crud: {_crud.get_entities()}")
        
        @_app.on_event("startup")
        async def on_startup():
            await startup_event()
        
        define_routes(_app, _crud)
    else:
        log.debug("App already created")

    return _app
