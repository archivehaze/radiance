from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('config')

csrf = CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import views, models