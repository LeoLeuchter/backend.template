"""
Module containing User data models for application.

This module defines two classes: UserBase and UserFull, both derived from Pydantic BaseModel.
These classes represent the structure of user data in the application, with UserBase as a base model
containing common attributes like user_name, name, and password_hash, and UserFull extending it by
adding an id attribute.
"""

from pydantic import BaseModel


class UserBase(BaseModel):
    """
    Represents the base structure of a User object in the application.

    Attributes:
        user_name (str): The username for the user.
        name (str): The full name of the user.
        password_hash (str): The hashed password of the user.
        is_admin (bool): Whether the user is an admin.
    """

    user_name: str
    name: str
    password_hash: str
    is_admin: bool = False


class UserFull(UserBase):
    """
    Represents a complete User object in the application, inheriting from UserBase and adding an
    id attribute.

    Attributes:
        id (int): The unique identifier for the user.
        is_admin (bool): Whether the user is an admin.
    """

    id: int


class UserFilter(BaseModel):
    """
    Represents a filter for users.

    Attributes:
        user_name (str | None): The username of the user to filter by.
        name (str | None): The name of the user to filter by.
        id (str | None): The ID of the user to filter by.
        use_and (bool): Determines whether to use 'AND' operator for multiple filters (Default: True).
    """

    user_name: str | None = None
    name: str | None = None
    id: int | None = None
    use_and: bool = True
