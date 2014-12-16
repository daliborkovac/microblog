#!/home/dkovac/virtualenv/python3.4_flask/bin/python
# This script is used for upgrading your database objects (a model) to their latest versions.
# When you are ready to release the new version of the app to your production server you just
# need to record a new migration, copy the migration scripts to your production server and run
# this simple script that applies the changes for you.
# See more about this on http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('Current database version: ' + str(v))
