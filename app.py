from flask import Flask, send_from_directory
from flask_mysqldb import MySQL
from flask_session import Session
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["MYSQL_HOST"]          = os.environ.get("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"]          = os.environ.get("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"]      = os.environ.get("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"]            = os.environ.get("MYSQL_DB", "ticketclassify")
app.config["MYSQL_CURSORCLASS"]   = "DictCursor"
app.config["SESSION_TYPE"]        = "filesystem"


UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"]       = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"]  = 5 * 1024 * 1024  

mysql = MySQL(app)
Session(app)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

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
