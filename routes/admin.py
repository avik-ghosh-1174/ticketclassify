from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
CATEGORIES = ['maintenance','internet','electricity','cleanliness','security','others']
SPECIALIZATION_LABELS = {
    'maintenance': 'Maintenance Staff', 'internet': 'IT Staff',
    'electricity': 'Electrician',       'cleanliness': 'Cleaner',
    'security':    'Security Guard',    'others':   'General Staff',
}

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.select_role"))
        if session.get("role") != "admin":
            from routes.auth import redirect_by_role
            return redirect_by_role(session.get("role"))
        return f(*args, **kwargs)
    return decorated

def get_db():
    from app import mysql
    return mysql

@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    db = get_db(); cur = db.connection.cursor()
    cur.execute("""SELECT t.*, u.full_name, u.email, u.role as user_role
                   FROM tickets t JOIN users u ON t.user_id=u.id
                   ORDER BY t.needs_review DESC, t.created_at DESC""")
    tickets = cur.fetchall()
    cur.execute("SELECT COUNT(*) as c FROM tickets"); total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM tickets WHERE status='pending'"); pending = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM tickets WHERE status='resolved'"); resolved = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='student'"); students = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='hall_staff'"); staff_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM tickets WHERE needs_review=1"); flagged = cur.fetchone()["c"]
    cur.close()
    return render_template("admin_dashboard.html", tickets=tickets, total=total,
                           pending=pending, resolved=resolved, students=students,
                           staff_count=staff_count, flagged=flagged)

@admin_bp.route("/ticket/<int:ticket_id>", methods=["GET","POST"])
@admin_required
def manage_ticket(ticket_id):
    db = get_db(); cur = db.connection.cursor()
    if request.method == "POST":
        status        = request.form["status"]
        corrected_cat = request.form.get("category")
        original_cat  = request.form.get("original_category")
        title         = request.form.get("title_hidden","")
        description   = request.form.get("description_hidden","")
        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (status, ticket_id))
        if corrected_cat and corrected_cat != original_cat:
            from ai_classifier import learn_from_correction
            learn_from_correction(ticket_id, corrected_cat, title, description, db.connection)
            flash(f"Status updated & AI learned: '{original_cat}' → '{corrected_cat}'.", "success")
        else:
            cur.execute("UPDATE tickets SET needs_review=0 WHERE id=%s", (ticket_id,))
            db.connection.commit()
            flash("Ticket updated.", "success")
        cur.close()
        return redirect(url_for("admin.dashboard"))
    cur.execute("""SELECT t.*, u.full_name, u.email FROM tickets t
                   JOIN users u ON t.user_id=u.id WHERE t.id=%s""", (ticket_id,))
    ticket = cur.fetchone(); cur.close()
    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_ticket.html", ticket=ticket, categories=CATEGORIES)

@admin_bp.route("/flagged")
@admin_required
def flagged_tickets():
    db = get_db(); cur = db.connection.cursor()
    cur.execute("""SELECT t.*, u.full_name, u.email FROM tickets t
                   JOIN users u ON t.user_id=u.id WHERE t.needs_review=1
                   ORDER BY t.created_at DESC""")
    tickets = cur.fetchall(); cur.close()
    return render_template("admin_flagged.html", tickets=tickets, categories=CATEGORIES)

@admin_bp.route("/users")
@admin_required
def manage_users():
    db = get_db(); cur = db.connection.cursor()
    cur.execute("SELECT id, full_name, email, role, specialization, created_at FROM users ORDER BY role, created_at DESC")
    users = cur.fetchall(); cur.close()
    return render_template("admin_user.html", users=users, spec_labels=SPECIALIZATION_LABELS)

@admin_bp.route("/users/create", methods=["GET","POST"])
@admin_required
def create_user():
    if request.method == "POST":
        name           = request.form["full_name"].strip()
        email          = request.form["email"].strip().lower()
        password       = request.form["password"]
        role           = request.form["role"]
        specialization = request.form.get("specialization") if role == "hall_staff" else None
        if role not in ("student","hall_staff","admin"):
            flash("Invalid role.", "error")
            return render_template("admin_create_user.html", spec_labels=SPECIALIZATION_LABELS)
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db = get_db(); cur = db.connection.cursor()
        try:
            cur.execute("INSERT INTO users (full_name,email,password_hash,role,specialization) VALUES (%s,%s,%s,%s,%s)",
                        (name, email, pw_hash, role, specialization))
            db.connection.commit()
            flash(f"Account created successfully.", "success")
            return redirect(url_for("admin.manage_users"))
        except Exception:
            flash("Email already exists.", "error")
        finally:
            cur.close()
    return render_template("admin_create_user.html", spec_labels=SPECIALIZATION_LABELS)
