"""
models/challenge_model.py
"""
from db import get_db_connection


def get_all_challenges():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            c.challengeID,
            c.challengeName,
            c.isActive,
            c.createdAt,
            u.userName AS createdByName,
            COUNT(cp.challengePlansID) AS plan_count
        FROM Challenges c
        LEFT JOIN Users u         ON u.userID      = c.createdBy
        LEFT JOIN Challenge_Plans cp ON cp.challengeID = c.challengeID
            AND cp.isActive = 1
        GROUP BY c.challengeID
        ORDER BY c.createdAt DESC
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def get_challenge_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            COUNT(*)                                          AS total,
            SUM(c.isActive = 1)                              AS active,
            SUM(c.challengeID IN (
                SELECT DISTINCT challengeID FROM Challenge_Plans WHERE isActive = 1
            ))                                               AS with_plans
        FROM Challenges c
    """)
    row = cursor.fetchone()
    cursor.close(); conn.close()
    total      = int(row['total']      or 0)
    active     = int(row['active']     or 0)
    with_plans = int(row['with_plans'] or 0)
    return {
        'total':      total,
        'active':     active,
        'with_plans': with_plans,
        'no_plan':    total - with_plans,
    }


def get_plans_for_challenge(challenge_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            cp.challengePlansID,
            cp.planName,
            cp.createdAt,
            u.userName AS createdByName
        FROM Challenge_Plans cp
        LEFT JOIN Users u ON u.userID = cp.createdBy
        WHERE cp.challengeID = %s AND cp.isActive = 1
        ORDER BY cp.createdAt ASC
    """, (challenge_id,))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    # Stringify dates for JSON
    for r in rows:
        r['createdAt'] = r['createdAt'].strftime('%d %b %Y') if r['createdAt'] else None
    return rows


def create_challenge(name: str, is_active: int, user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Challenges (challengeName, isActive, createdBy)
        VALUES (%s, %s, %s)
    """, (name, is_active, user_id))
    conn.commit()
    cursor.close(); conn.close()


def create_challenge_plan(challenge_id: int, plan_name: str, user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Challenge_Plans (planName, challengeID, createdBy, isActive)
        VALUES (%s, %s, %s, 1)
    """, (plan_name, challenge_id, user_id))
    conn.commit()
    cursor.close(); conn.close()