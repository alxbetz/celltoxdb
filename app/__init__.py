import logging

from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from flask_migrate import Migrate
from flask_caching import Cache

"""
 Logging configuration
"""

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = SQLA(app)
appbuilder = AppBuilder(app, db.session)
migrate = Migrate(app,db)
cache = Cache(app)

from app.plotlydash.dashboard import create_dashboard
app = create_dashboard(app)

# Compile CSS
#from app.assets import compile_assets
#compile_assets(app)


"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""

from . import views

