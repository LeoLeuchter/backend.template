from pydantic import BaseModel


class PersonBase(BaseModel):
    """
    Represents the base structure of a Person object in the application.

    Attributes:
        first_name (str): The first name of the person.
        last_name (str): The last name of the person.
    """
    first_name: str
    last_name: str


class PersonFull(PersonBase):
    """
    Represents a complete Person object in the application, inheriting from PersonBase and adding an
    id attribute.

    Attributes:
        id (int): The unique identifier for the person.
    """

    id: int


class PersonFilter(BaseModel):
    """
    Represents a filter for persons.

    Attributes:
        first_name (str | None): The first name of the person to filter by.
        last_name (str | None): The last name of the person to filter by.
        id (int | None): The ID of the person to filter by.
        use_and (bool): Determines whether to use 'AND' operator for multiple filters (Default: True).
    """

    first_name: str | None = None
    last_name: str | None = None
    id: int | None = None
    use_and: bool = True
