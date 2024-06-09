from planner import config

config.in_memory = True
from pytest import fixture

from planner import database, models


@fixture(scope="session")
def setup_db():
    models.create_tables()


@fixture
def rollback_transaction(setup_db):
    with database.DB().atomic() as transaction:
        yield
        transaction.rollback()
