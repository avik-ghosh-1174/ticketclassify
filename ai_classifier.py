import re

CATEGORIES = ['maintenance', 'internet', 'electricity', 'cleanliness', 'security', 'others']
CONFIDENCE_THRESHOLD = 50.0   

def _tokenize(text):
    """Lowercase, strip punctuation, split into words."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [w for w in text.split() if len(w) > 2]

def classify_ticket(title, description, db_connection):
    """
    Classify a ticket using keyword weights from DB.
    Returns: (category, confidence_score, needs_review)
    """
    tokens = _tokenize(f"{title} {description}")
    if not tokens:
        return "others", 0.0, True

    
    cur = db_connection.cursor()
    cur.execute("SELECT keyword, category, weight FROM category_training")
    rows = cur.fetchall()
    cur.close()

    
    kw_map = {}
    for row in rows:
        kw  = row["keyword"]
        cat = row["category"]
        wt  = row["weight"]
        if kw not in kw_map:
            kw_map[kw] = {}
        kw_map[kw][cat] = wt

    
    scores = {cat: 0 for cat in CATEGORIES}
    for token in tokens:
        if token in kw_map:
            for cat, wt in kw_map[token].items():
                scores[cat] += wt

    total = sum(scores.values())
    if total == 0:
        return "others", 0.0, True

    
    best_cat   = max(scores, key=scores.get)
    best_score = scores[best_cat]
    confidence = round((best_score / total) * 100, 2)

    needs_review = confidence < CONFIDENCE_THRESHOLD
    return best_cat, confidence, needs_review


def learn_from_correction(ticket_id, correct_category, title, description, db_connection):
    """
    When admin corrects a category, extract tokens from the ticket and
    increase their weight for the correct category in category_training.
    """
    tokens = _tokenize(f"{title} {description}")
    if not tokens:
        return

    cur = db_connection.cursor()
    for token in set(tokens):          
        cur.execute("""
            INSERT INTO category_training (keyword, category, weight)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE weight = weight + 1
        """, (token, correct_category))

    
    cur.execute("""
        UPDATE tickets
        SET category=%s, admin_corrected=1, needs_review=0
        WHERE id=%s
    """, (correct_category, ticket_id))

    db_connection.commit()
    cur.close()
