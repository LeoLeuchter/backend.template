from typing import override

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base
from ._entity import Entity


class User(Base):
    """
    Represents a User in the application. The User class is mapped to the 'users' table and has
    properties for user name, entity ID, and password hash.

    Attributes:
        __tablename__ (str): The name of the database table that this class is mapped to.
        user_name (Mapped[str]): The unique username of the user.
        entity_id (Mapped[int]): The ID of the associated Entity.
        password_hash (Mapped[str]): The hashed password of the user.
        entity (Mapped[Entity]): The associated Entity object.
    """

    __tablename__: str = "users"

    user_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey(column=Entity.id), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    entity: Mapped[Entity] = relationship()

    @property
    def name(self) -> str:
        return self.entity.name

    @name.setter
    def name(self, value:str):
        self.entity.name=value

    @override
    def __repr__(self) -> str:
        return f"User(user_name='{self.user_name}', password_hash='{self.password_hash}', entity={repr(self.entity)})"
