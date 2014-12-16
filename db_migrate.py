#!/home/dkovac/virtualenv/python3.4_flask/bin/python
# This is a script for recording migrations (changes to our database, new tables, columns and stuff).
# This script reads model in our application (looks for classes that extend db.Model) and compares it to
# the current state of the database. Then it makes the needed changes in the database to synchronize its
# model to the model defined in the application. It also generates a migration script that is used for
# automatic apply of these changes to other instances (e.g. migration recorded on DEV and applied to TEST or PROD).
# This script is fully generic (you need not change anything in it). It automatically detects the changes
# from the previous migration.
# See more about this on http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
import imp
from migrate.versioning import api
from app import db
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migration.py' % (v+1))
tmp_module = imp.new_module('old_model')
old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
exec(old_model, tmp_module.__dict__)
script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, tmp_module.meta, db.metadata)
open(migration, "wt").write(script)
api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('New migration saved as ' + migration)
print('Current database version: ' + str(v))
