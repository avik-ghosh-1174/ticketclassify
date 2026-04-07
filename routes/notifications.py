import MySQLdb.cursors

def _dict_cursor(db_connection):
    """Always return a DictCursor regardless of connection defaults."""
    return db_connection.cursor(MySQLdb.cursors.DictCursor)

def auto_route_ticket(ticket_id, category, db_connection):
    """
    Find hall_staff with matching specialization.
    Set ticket status to 'assigned' and send them a notification.
    """
    try:
        cur = _dict_cursor(db_connection)
        cur.execute(
            "SELECT id, full_name FROM users "
            "WHERE role='hall_staff' AND specialization=%s LIMIT 1",
            (category,)
        )
        staff = cur.fetchone()          
        if staff:
           
            cur.execute(
                "UPDATE tickets SET status='assigned' WHERE id=%s",
                (ticket_id,)
            )
            db_connection.commit()

           
            cur.execute(
                "INSERT INTO notifications (user_id, ticket_id, message) "
                "VALUES (%s, %s, %s)",
                (staff["id"], ticket_id,
                 f"A new '{category}' ticket has been routed to you.")
            )
            db_connection.commit()
        cur.close()
    except Exception as e:
        
        import traceback
        print(f"[auto_route_ticket ERROR] {e}")
        traceback.print_exc()

def notify_student_on_update(ticket_id, new_status, db_connection):
    """Notify the ticket owner whenever staff/admin changes the status."""
    try:
        cur = _dict_cursor(db_connection)
        cur.execute(
            "SELECT user_id FROM tickets WHERE id=%s",
            (ticket_id,)
        )
        row = cur.fetchone()           
        if row:
            label = new_status.replace("_", " ").title()
            cur.execute(
                "INSERT INTO notifications (user_id, ticket_id, message) "
                "VALUES (%s, %s, %s)",
                (row["user_id"], ticket_id,
                 f"Your ticket #{ticket_id} status was updated to: {label}.")
            )
            db_connection.commit()
        cur.close()
    except Exception as e:
        import traceback
        print(f"[notify_student_on_update ERROR] {e}")
        traceback.print_exc()

def unread_count(user_id, db_connection):
    """Return unread notification count for sidebar badge."""
    try:
        cur = _dict_cursor(db_connection)
        cur.execute(
            "SELECT COUNT(*) as c FROM notifications "
            "WHERE user_id=%s AND is_read=0",
            (user_id,)
        )
        count = cur.fetchone()["c"]     
        cur.close()
        return count
    except Exception as e:
        print(f"[unread_count ERROR] {e}")
        return 0