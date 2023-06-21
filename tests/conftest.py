from pytest import fixture

from planner import models


@fixture(scope="session")
def setup_db():
    models.create_tables()


@fixture
def rollback_transaction(setup_db):
    with models.db.atomic() as transaction:
        yield
        transaction.rollback()
