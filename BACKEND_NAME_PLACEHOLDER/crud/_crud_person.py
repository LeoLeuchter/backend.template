from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_logger
from ..model import Entity, Person
from ..schema import EntityBase, EntityFull, PersonBase, PersonFilter, PersonFull
from ._crud_entity import CrudEntity
from ._error_messages import ERROR_MESSAGES

log = get_logger()


class CrudPerson(CrudEntity):

    def change_person(self, person: PersonFull):
        with Session(bind=self._engine) as session:
            stmt = select(Person).where(Person.id == person.id)
            result = list(session.execute(stmt).scalars())
            if len(result) != 1:
                raise AttributeError(
                    ERROR_MESSAGES.NO_SUCH_ID % (Person.__name__, person.id)
                )
            change_person = result[0]
            change_person.first_name = person.first_name
            change_person.last_name = person.last_name
            session.add(change_person)
            session.commit()

    def delete_person(self, id: int):
        """
        Delete an existing person identified by its id.

        Args:
            id (int): The id of the person to be deleted

        Raises:
            AttributeError if no person with the given ID exists!
        """
        with Session(bind=self._engine) as session:
            stmt = delete(Person).where(Person.id == id)
            result = session.execute(stmt)
            if (
                not result.rowcount  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
            ):
                raise AttributeError(ERROR_MESSAGES.NO_SUCH_ID % (Person.__name__, id))
            session.commit()

    def create_person(
        self, new_person: PersonBase, existing_entity: EntityFull | None = None
    ) -> PersonFull:
        """
        Creates a new PersonFull object in the database by saving a new person object and associating it with an Entity.

        Args:
            new_person (PersonBase): The new person to be created with first_name and last_name.
            existing_entity (EntityFull | None): Optional existing entity to associate with person.

        Returns:
            PersonFull: A new PersonFull object representing the newly created person.
        """
        with Session(bind=self._engine) as session:
            person = Person()
            person.first_name = new_person.first_name
            person.last_name = new_person.last_name

            entity: Entity | None = None
            if existing_entity:
                entity = self._get_entity(session, existing_entity)
                if not entity:
                    raise AttributeError(
                        ERROR_MESSAGES.NO_SUCH_ID
                        % (Entity.__name__, existing_entity.id)
                    )
            try:
                if not entity:
                    # Create new entity with full name
                    full_name = f"{new_person.first_name} {new_person.last_name}"
                    new_entity = EntityBase(name=full_name)
                    entity = self._create_entity(session, new_entity)

                person.entity = entity
                session.add(person)
                session.commit()
                person_full = PersonFull(
                    first_name=person.first_name,
                    last_name=person.last_name,
                    id=person.id,
                )
                return person_full
            except IntegrityError as exc:
                log.error(f"IntegrityError: {exc.detail}")
                raise AttributeError(
                    ERROR_MESSAGES.DUPLICATE_ENTRY
                    % (person.__class__.__name__, "first_name/last_name", f"{new_person.first_name} {new_person.last_name}")
                )

    def get_persons(self, filter: PersonFilter | None = None) -> list[PersonFull]:
        """
        Fetches a list of PersonFull objects from the database.

        Args:
            filter (PersonFilter | None): Optional filter for persons by first_name, last_name, or id.

        Returns:
            list[PersonFull]: A list of PersonFull objects representing the fetched persons.
        """
        with Session(bind=self._engine) as session:
            full_persons: list[PersonFull] = []
            stmt = select(Person)
            if filter and filter.first_name:
                stmt = stmt.where(Person.first_name.like(f"%{filter.first_name}%"))
            if filter and filter.last_name:
                stmt = stmt.where(Person.name.like(f"%{filter.last_name}%"))
            if filter and filter.id:
                stmt = stmt.where(Person.id == filter.id)

            log.debug(f"Filter:{stmt}")
            for orm_person in session.execute(stmt).scalars().all():
                full_persons.append(
                    PersonFull(
                        id=orm_person.id,
                        first_name=orm_person.first_name,
                        last_name=orm_person.last_name,
                    )
                )
            return full_persons
