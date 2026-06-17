import json
import logging
import os

"""
A class for managing database configuration. Provides a singleton pattern and a method to 
load the configuration from a file.

Attributes:
    DB_CONNECTION_STRING (str): Default SQLite in-memory database connection string.
    __instances (dict[str, Config]): A dictionary storing instances of this class keyed by 
                                     their associated file names.

Methods:
    __init__(self, file_name: str = ""): Initializes a new instance with an optional file 
                                         name for loading the configuration.
    _load(self, filename: str) -> None: Loads the database connection string from a JSON file.
    connection_string(self) -> str: Returns the current database connection string.
    get_instance(cls, file_name: str = "") -> Config: Retrieves an instance of this class 
                                              associated with the given file name, creating a 
                                              new one if it doesn't exist yet.
"""


class Config:

    DB_CONNECTION_STRING: str = "sqlite:///:memory:"
    __instances: dict[str, "Config"] = {}

    KEY_CONNECTION_STRING: str = "connection_string"
    KEY_LOG_LEVEL: str = "log_level"

    def __init__(self, file_name: str = ""):
        if file_name in Config.__instances:
            raise RuntimeError("Don't Call constructor!")
        Config.__instances[file_name] = self
        if file_name:
            self._load(file_name)
        else:
            self._log_level: int | None = None
            self._connection_string: str = Config.DB_CONNECTION_STRING

    def _load(self, filename: str) -> None:
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                config_file: dict[str, str] = json.load(f)  # pyright: ignore[reportAny]
                self._connection_string = config_file[Config.KEY_CONNECTION_STRING]
                level_name: str | None = None
                if Config.KEY_LOG_LEVEL in config_file:
                    level_name = config_file[Config.KEY_LOG_LEVEL]
                if level_name and type(level_name) == str:
                    level_mappings = logging.getLevelNamesMapping()
                    if level_name in level_mappings:
                        self._log_level = level_mappings[level_name]

    """
    Get the current connection string.

    Returns:
        str: The connection string for the database.
    """

    @property
    def connection_string(self) -> str:
        return self._connection_string

    """
    Get the current log_level.
    Returns:
        str | None: The log level or None, if not specified.
    """

    @property
    def log_level(self) -> int | None:
        return self._log_level

    @classmethod
    def get_instance(cls, file_name: str = "") -> "Config":
        """
        Returns an instance of the Config class with the given file name. If no file name is provided,
        it will use the default connection string. If an instance already exists for the provided file
        name, it will return that instance instead of creating a new one.

        :param file_name: The file name of the configuration file (optional)
        :return: An instance of the Config class
        """
        if not file_name and "CONFIG_FILE" in os.environ:
            file_name = os.environ["CONFIG_FILE"]
        if file_name in cls.__instances:
            return cls.__instances[file_name]
        return Config(file_name)
