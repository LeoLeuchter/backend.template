from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_logger
from ..model import Entity, User
from ..schema import EntityBase, EntityFull, UserBase, UserFilter, UserFull
from ._crud_entity import CrudEntity
from ._error_messages import ERROR_MESSAGES

log = get_logger()
"""
CrudUsers - CRUD operations for User entities.

This module provides methods for creating, retrieving, updating, and deleting User objects in a
database. The User objects are related to EntityBase objects through the CrudEntity class.
"""


class CrudUsers(CrudEntity):

    def change_user(self, user: UserFull):
        with Session(bind=self._engine) as session:
            stmt = select(User).where(User.entity_id == user.id)
            result = list(session.execute(stmt).scalars())
            if len(result) != 1:
                raise AttributeError(
                    ERROR_MESSAGES.NO_SUCH_ID % (User.__name__, user.id)
                )
            change_user = result[0]
            change_user.password_hash = user.password_hash
            change_user.name = user.name
            change_user.user_name = user.user_name
            change_user.is_admin = user.is_admin
            session.add(change_user)
            session.commit()

    def delete_user(self, id: int):
        """
        Delete an existing User identified by its id.

        Args:
            id (int): The id of the user to be deleted

        Raises:
            AttributeError if no user with the given ID exists!
        """
        with Session(bind=self._engine) as session:
            stmt = delete(User).where(User.entity_id.is_(id))
            result = session.execute(stmt)
            log.error(f"Result Type is: {type(result)}")
            if (
                not result.rowcount  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
            ):
                raise AttributeError(ERROR_MESSAGES.NO_SUCH_ID % (User.__name__, id))
            session.commit()

    def create_user(
        self, new_user: UserBase, existing_entity: EntityFull | None = None
    ) -> UserFull:
        """
        Creates a new UserFull object in the database by saving a new User object and associating it with an EntityBase.

        Args:
            new_user (UserBase): The new user to be created, containing user_name, password_hash, name, and is_admin attributes.

        Returns:
            UserFull: A new UserFull object representing the newly created user.
        """
        with Session(bind=self._engine) as session:
            user = User()
            user.user_name = new_user.user_name
            user.password_hash = new_user.password_hash
            user.is_admin = new_user.is_admin

            entity: Entity | None = None
            if existing_entity:
                entity = self._get_entity(session, existing_entity)
                if not entity:
                    raise AttributeError(
                        ERROR_MESSAGES.NO_SUCH_ID
                        % (Entity.__name__, existing_entity.id)
                    )
                if new_user.name:
                    entity.name = new_user.name
            try:
                if not entity:
                    new_entity = EntityBase(name=new_user.name)
                    entity = self._create_entity(session, new_entity)

                user.entity = entity
                session.add(user)
                session.commit()
                user_full = UserFull(
                    user_name=user.user_name,
                    name=entity.name,
                    password_hash=user.password_hash,
                    id=user.entity_id,
                    is_admin=user.is_admin,
                )
                return user_full
            except IntegrityError as exc:
                log.error(f"IntegrityError: {exc.detail}")
                raise AttributeError(
                    ERROR_MESSAGES.DUPLICATE_ENTRY
                    % (user.__class__.__name__, "user_name", user.user_name)
                )

    def get_users(self, filter: UserFilter | None = None) -> list[UserFull]:
        """
        Fetches a list of UserFull objects from the database. If a filter is provided, it filters
        the users based on the provided string in their user_name or name fields.

        Args:
            filter (str | None, optional): A string that can be used to filter users by user_name
                                           or name. Defaults to None which means no filtering.

        Returns:
            list[UserFull]: A list of UserFull objects representing the fetched users.
        """
        with Session(bind=self._engine) as session:
            full_users: list[UserFull] = []
            stmt = select(User)
            if filter and filter.user_name:
                stmt = stmt.where(User.user_name.like(filter.user_name))
            if filter and filter.name:
                stmt = stmt.where(Entity.id == User.entity_id).where(
                    Entity.name.like(filter.name)
                )
            if filter and filter.id:
                stmt = stmt.where(User.entity_id == filter.id)

            log.debug(f"Filter:{stmt}")
            for orm_user in session.execute(stmt).scalars().all():
                full_users.append(
                    UserFull(
                        id=orm_user.entity_id,
                        name=orm_user.entity.name,
                        user_name=orm_user.user_name,
                        password_hash=orm_user.password_hash,
                        is_admin=orm_user.is_admin,
                    )
                )
            return full_users

    def get_user_by_username(self, user_name: str):
        with Session(bind=self._engine) as session:
            stmt = select(User).where(User.user_name == user_name)
            result = list(session.execute(stmt).scalars())
            if len(result) != 1:
                return None
            return result[0]
