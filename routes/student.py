from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os, uuid

student_bp = Blueprint("student", __name__, url_prefix="/student")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
ALLOWED_EXT = {"png","jpg","jpeg","gif","pdf","docx","txt"}

def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.select_role"))
        if session.get("role") != "student":
            from routes.auth import redirect_by_role
            return redirect_by_role(session.get("role"))
        return f(*args, **kwargs)
    return decorated

def get_db():
    from app import mysql
    return mysql

def allowed_file(f):
    return "." in f and f.rsplit(".",1)[1].lower() in ALLOWED_EXT

@student_bp.route("/dashboard")
@student_required
def dashboard():
    db = get_db(); cur = db.connection.cursor()
    cur.execute("SELECT * FROM tickets WHERE user_id=%s ORDER BY created_at DESC", (session["user_id"],))
    tickets = cur.fetchall()
    cur.execute("SELECT COUNT(*) as c FROM tickets WHERE user_id=%s", (session["user_id"],))
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM tickets WHERE user_id=%s AND status='resolved'", (session["user_id"],))
    resolved = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM tickets WHERE user_id=%s AND status='pending'", (session["user_id"],))
    pending = cur.fetchone()["c"]
    cur.close()
    return render_template("student_dashboard.html", tickets=tickets, total=total, resolved=resolved, pending=pending)

@student_bp.route("/submit", methods=["GET","POST"])
@student_required
def submit_ticket():
    if request.method == "POST":
        title       = request.form["title"].strip()
        description = request.form["description"].strip()
        urgency     = request.form["urgency"]
        attachment  = None

        file = request.files.get("attachment")
        if file and file.filename and allowed_file(file.filename):
            ext      = file.filename.rsplit(".",1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            attachment = filename

        # ── Module 2: AI Classification ──────────────
        from ai_classifier import classify_ticket
        db = get_db()
        category, confidence, needs_review = classify_ticket(title, description, db.connection)
        # ─────────────────────────────────────────────

        cur = db.connection.cursor()
        cur.execute("""INSERT INTO tickets
                       (user_id, title, description, urgency, attachment,
                        category, confidence_score, needs_review)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (session["user_id"], title, description, urgency, attachment,
                     category, confidence, int(needs_review)))
        db.connection.commit()
        cur.close()

        flash(f"Ticket submitted! AI classified it as <strong>{category}</strong> "
              f"(confidence: {confidence}%).", "success")
        return redirect(url_for("student.dashboard"))
    return render_template("submit_ticket.html")

@student_bp.route("/ticket/<int:ticket_id>")
@student_required
def view_ticket(ticket_id):
    db = get_db(); cur = db.connection.cursor()
    cur.execute("SELECT * FROM tickets WHERE id=%s AND user_id=%s", (ticket_id, session["user_id"]))
    ticket = cur.fetchone(); cur.close()
    if not ticket:
        flash("Ticket not found.", "error")
        return redirect(url_for("student.dashboard"))
    return render_template("view_ticket.html", ticket=ticket, back_url=url_for("student.dashboard"))
