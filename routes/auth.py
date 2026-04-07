from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt, re

auth_bp = Blueprint("auth", __name__)

SPECIALIZATIONS = {
    'maintenance':  'Maintenance Staff',
    'internet':     'IT Staff',
    'electricity':  'Electrician',
    'cleanliness':  'Cleaner',
    'security':     'Security Guard',
    'others':       'General Staff',
}

def get_db():
    from app import mysql
    return mysql

def valid_email(email):
    return re.match(r"^[\w\.-]+@diu\.edu\.bd$", email)

def redirect_by_role(role):
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif role == "hall_staff":
        return redirect(url_for("staff.dashboard"))
    else:
        return redirect(url_for("student.dashboard"))

@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect_by_role(session.get("role"))
    return redirect(url_for("auth.select_role"))

@auth_bp.route("/select-role")
def select_role():
    if "user_id" in session:
        return redirect_by_role(session.get("role"))
    return render_template("select_role.html")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    role = request.args.get("role", request.form.get("role", "student"))
    if role not in ("student","hall_staff","admin"):
        return redirect(url_for("auth.select_role"))

    if request.method == "POST":
        email    = request.form["email"].strip().lower()
        password = request.form["password"]
        role     = request.form["role"]

        db = get_db()
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND role=%s", (email, role))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            session["user_id"]         = user["id"]
            session["user_name"]       = user["full_name"]
            session["role"]            = user["role"]
            session["specialization"]  = user.get("specialization")
            return redirect_by_role(user["role"])
        flash("Invalid email or password for this role.", "error")

    return render_template("login.html", role=role)

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    role = request.args.get("role", request.form.get("role", "student"))
    if role not in ("student", "hall_staff"):
        role = "student"

    if request.method == "POST":
        name           = request.form["full_name"].strip()
        email          = request.form["email"].strip().lower()
        password       = request.form["password"]
        confirm        = request.form["confirm_password"]
        role           = request.form.get("role", "student")
        specialization = request.form.get("specialization") if role == "hall_staff" else None

        if role not in ("student", "hall_staff"):
            role = "student"
        if not valid_email(email):
            flash("Only @diu.edu.bd institutional emails are allowed.", "error")
            return render_template("register.html", role=role, specializations=SPECIALIZATIONS)
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html", role=role, specializations=SPECIALIZATIONS)
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("register.html", role=role, specializations=SPECIALIZATIONS)
        if role == "hall_staff" and specialization not in SPECIALIZATIONS:
            flash("Please select a valid specialization.", "error")
            return render_template("register.html", role=role, specializations=SPECIALIZATIONS)

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db = get_db()
        cur = db.connection.cursor()
        try:
            cur.execute("""INSERT INTO users (full_name, email, password_hash, role, specialization)
                           VALUES (%s,%s,%s,%s,%s)""",
                        (name, email, pw_hash, role, specialization))
            db.connection.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login") + f"?role={role}")
        except Exception:
            flash("Email already registered.", "error")
        finally:
            cur.close()

    return render_template("register.html", role=role, specializations=SPECIALIZATIONS)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.select_role"))
