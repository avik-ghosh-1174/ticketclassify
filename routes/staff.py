from flask import Blueprint, render_template, request, redirect, url_for, session, flash

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

SPECIALIZATION_LABELS = {
    'maintenance': 'Maintenance Staff', 'internet':    'IT Staff',
    'electricity': 'Electrician',       'cleanliness': 'Cleaner',
    'security':    'Security Guard',    'others':      'General Staff',
}
SPECIALIZATION_ICONS = {
    'maintenance': 'fa-screwdriver-wrench', 'internet':    'fa-wifi',
    'electricity': 'fa-bolt',              'cleanliness': 'fa-broom',
    'security':    'fa-shield-halved',     'others':      'fa-helmet-safety',
}

def staff_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.select_role"))
        if session.get("role") != "hall_staff":
            from routes.auth import redirect_by_role
            return redirect_by_role(session.get("role"))
        return f(*args, **kwargs)
    return decorated

def get_db():
    from app import mysql
    return mysql

@staff_bp.route("/dashboard")
@staff_required
def dashboard():
    db = get_db(); cur = db.connection.cursor()
    cur.execute("SELECT specialization FROM users WHERE id=%s", (session["user_id"],))
    row = cur.fetchone()
    specialization = row["specialization"] if row else None

    if specialization and specialization != "others":
        cur.execute("""SELECT t.*, u.full_name, u.email FROM tickets t
                       JOIN users u ON t.user_id=u.id
                       WHERE t.category=%s OR t.category IS NULL
                       ORDER BY FIELD(t.urgency,'critical','high','medium','low'),
                                t.created_at DESC""", (specialization,))
    else:
        cur.execute("""SELECT t.*, u.full_name, u.email FROM tickets t
                       JOIN users u ON t.user_id=u.id
                       WHERE t.category='others' OR t.category IS NULL
                       ORDER BY FIELD(t.urgency,'critical','high','medium','low'),
                                t.created_at DESC""")
    tickets = cur.fetchall()

    total    = len(tickets)
    pending  = sum(1 for t in tickets if t["status"] == "pending")
    assigned = sum(1 for t in tickets if t["status"] == "assigned")
    inprog   = sum(1 for t in tickets if t["status"] == "in_progress")
    resolved = sum(1 for t in tickets if t["status"] == "resolved")

    from routes.notifications import unread_count
    unread = unread_count(session["user_id"], db.connection)
    cur.close()

    return render_template("staff_dashboard.html",
                           tickets=tickets, total=total,
                           pending=pending, assigned=assigned,
                           inprog=inprog, resolved=resolved,
                           specialization=specialization,
                           spec_label=SPECIALIZATION_LABELS.get(specialization, "General Staff"),
                           spec_icon=SPECIALIZATION_ICONS.get(specialization, "fa-helmet-safety"),
                           unread=unread)

@staff_bp.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
@staff_required
def handle_ticket(ticket_id):
    db = get_db(); cur = db.connection.cursor()
    cur.execute("SELECT specialization FROM users WHERE id=%s", (session["user_id"],))
    row = cur.fetchone()
    specialization = row["specialization"] if row else None

    if request.method == "POST":
        new_status = request.form["status"]
        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_status, ticket_id))
        db.connection.commit()
       
        from routes.notifications import notify_student_on_update
        notify_student_on_update(ticket_id, new_status, db.connection)
        flash("Ticket updated. Student has been notified.", "success")
        cur.close()
        return redirect(url_for("staff.dashboard"))

    if specialization and specialization != "others":
        cur.execute("""SELECT t.*, u.full_name, u.email FROM tickets t
                       JOIN users u ON t.user_id=u.id
                       WHERE t.id=%s AND (t.category=%s OR t.category IS NULL)""",
                    (ticket_id, specialization))
    else:
        cur.execute("""SELECT t.*, u.full_name, u.email FROM tickets t
                       JOIN users u ON t.user_id=u.id WHERE t.id=%s""", (ticket_id,))
    ticket = cur.fetchone()
    cur.close()

    if not ticket:
        flash("You do not have access to this ticket.", "error")
        return redirect(url_for("staff.dashboard"))
    return render_template("staff_ticket.html", ticket=ticket,
                           spec_label=SPECIALIZATION_LABELS.get(specialization, "General Staff"))


@staff_bp.route("/notifications")
@staff_required
def notifications():
    db = get_db(); cur = db.connection.cursor()
    cur.execute("""SELECT n.*, t.title as ticket_title FROM notifications n
                   LEFT JOIN tickets t ON n.ticket_id=t.id
                   WHERE n.user_id=%s ORDER BY n.created_at DESC""",
                (session["user_id"],))
    notifs = cur.fetchall()
    cur.execute("UPDATE notifications SET is_read=1 WHERE user_id=%s",
                (session["user_id"],))
    db.connection.commit()
    cur.close()
    return render_template("staff_notifications.html", notifs=notifs)
