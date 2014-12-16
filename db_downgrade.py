#!/home/dkovac/virtualenv/python3.4_flask/bin/python
# This script is used for downgrading your database objects (a model) one revision down.
# You can run it multiple times to downgrade several revisions.
# See more about this on http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
api.downgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, v - 1)
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('Current database version: ' + str(v))
