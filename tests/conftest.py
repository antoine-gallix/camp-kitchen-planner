from planner import config, db

config.in_memory = True

from pytest import fixture
from planner import models


@fixture(scope="session")
def setup_db():
    models.create_tables()


@fixture
def rollback_transaction(setup_db):
    with db.atomic() as transaction:
        yield
        transaction.rollback()
