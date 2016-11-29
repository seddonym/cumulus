"""
Run this module to create the initial database tables.

    python project/sqlalchemy_insert.py

"""
import sys
from utils import create_cloudsql_engine
from models import Base


def _create_all():
    engine = create_cloudsql_engine()
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    sys.stdout.write('Creating database tables...')
    _create_all()
    sys.stdout.write('Done.')
