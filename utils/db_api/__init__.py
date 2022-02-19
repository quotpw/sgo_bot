from data.config import MYSQL_DATA
from .database_api import Sql

database = Sql(**MYSQL_DATA)
