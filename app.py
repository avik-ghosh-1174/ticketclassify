from flask import Flask
from flask_mysqldb import MySQL
from flask_session import Session
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["MYSQL_HOST"]        = os.environ.get("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"]        = os.environ.get("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"]    = os.environ.get("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"]          = os.environ.get("MYSQL_DB", "ticketclassify")
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config["SESSION_TYPE"]      = "filesystem"

mysql = MySQL(app)
Session(app)

from routes.auth    import auth_bp
from routes.student import student_bp
from routes.staff   import staff_bp
from routes.admin   import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)
