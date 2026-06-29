"""
models/user_model.py
"""
from db import get_db_connection
import hashlib


def _hash_password(password: str) -> str:
    """SHA-256 hash. Replace with bcrypt if you prefer."""
    return hashlib.sha256(password.encode()).hexdigest()


# ── Read ──────────────────────────────────────────────────────────────────────

def get_all_users() -> list:
    """
    Returns all users with their aggregated divisions and customers.
    Each user dict has:
        userID, userName, emailAddress, mobile, isSuperAdmin, userRole,
        isActive, createdAt,
        divisions: [str]  — division names
        customers: [str]  — customer names
        division_ids: [int]
        customer_ids: [int]
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            u.userID, u.userName, u.emailAddress, u.mobile,
            u.isSuperAdmin, u.userRole, u.isActive, u.createdAt
        FROM Users u
        ORDER BY u.createdAt DESC
    """)
    users = cursor.fetchall()

    if not users:
        cursor.close(); conn.close()
        return []

    user_ids = [u['userID'] for u in users]
    fmt      = ','.join(['%s'] * len(user_ids))

    # Division names per user
    cursor.execute(f"""
        SELECT ud.userID, d.divisionID, d.divisionName
        FROM User_Divisions ud
        JOIN Division d ON d.divisionID = ud.divisionID
        WHERE ud.userID IN ({fmt}) AND ud.isActive = 1
    """, user_ids)
    div_rows = cursor.fetchall()

    # Customer names per user
    cursor.execute(f"""
        SELECT uc.userID, c.customerID, c.customerName
        FROM User_Customers uc
        JOIN Customers c ON c.customerID = uc.customerID
        WHERE uc.userID IN ({fmt}) AND uc.isActive = 1
    """, user_ids)
    cust_rows = cursor.fetchall()

    cursor.close(); conn.close()

    # Build lookup dicts
    div_map  = {}
    divid_map = {}
    for r in div_rows:
        div_map.setdefault(r['userID'], []).append(r['divisionName'])
        divid_map.setdefault(r['userID'], []).append(r['divisionID'])

    cust_map  = {}
    custid_map = {}
    for r in cust_rows:
        cust_map.setdefault(r['userID'], []).append(r['customerName'])
        custid_map.setdefault(r['userID'], []).append(r['customerID'])

    for u in users:
        uid = u['userID']
        u['divisions']    = div_map.get(uid, [])
        u['division_ids'] = divid_map.get(uid, [])
        u['customers']    = cust_map.get(uid, [])
        u['customer_ids'] = custid_map.get(uid, [])

    return users


def get_user_stats() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            COUNT(*)                   AS total,
            SUM(isActive = 1)          AS active,
            SUM(isActive = 0)          AS inactive,
            SUM(isSuperAdmin = 1)      AS superadmin
        FROM Users
    """)
    row = cursor.fetchone()
    cursor.close(); conn.close()
    return {
        'total':      int(row['total']      or 0),
        'active':     int(row['active']     or 0),
        'inactive':   int(row['inactive']   or 0),
        'superadmin': int(row['superadmin'] or 0),
    }


def get_all_divisions_for_form() -> list:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT divisionID, divisionName FROM Division WHERE isActive=1 ORDER BY divisionName")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def get_all_customers_for_form() -> list:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT customerID, customerName FROM Customers WHERE isActive=1 ORDER BY customerName")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


# ── Write ─────────────────────────────────────────────────────────────────────

def create_user(user_data: dict, division_ids: list, customer_ids: list):
    """
    Inserts into Users, then User_Divisions, then User_Customers.
    Password is hashed before storage.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False

        hashed = _hash_password(user_data['userPassword'])

        cursor.execute("""
            INSERT INTO Users
                (userName, emailAddress, mobile, userPassword,
                 isSuperAdmin, userRole, isActive)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_data['userName'], user_data['emailAddress'],
            user_data.get('mobile'), hashed,
            user_data['isSuperAdmin'], user_data['userRole'],
            user_data['isActive'],
        ))
        user_id = cursor.lastrowid

        for did in division_ids:
            cursor.execute("""
                INSERT INTO User_Divisions (userID, divisionID, isActive)
                VALUES (%s, %s, 1)
            """, (user_id, did))

        for cid in customer_ids:
            cursor.execute("""
                INSERT INTO User_Customers (userID, customerID, isActive)
                VALUES (%s, %s, 1)
            """, (user_id, cid))

        conn.commit()
        return user_id

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close(); conn.close()


def update_user(user_id: int, update_data: dict, division_ids: list, customer_ids: list):
    """
    Updates user core fields, replaces division and customer access lists.
    If update_data['password'] is None, password is left unchanged.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False

        if update_data.get('password'):
            cursor.execute("""
                UPDATE Users
                SET userName=%s, emailAddress=%s, mobile=%s,
                    isSuperAdmin=%s, userRole=%s, isActive=%s,
                    userPassword=%s, updatedAt=NOW()
                WHERE userID=%s
            """, (
                update_data['userName'], update_data['emailAddress'],
                update_data.get('mobile'),
                update_data['isSuperAdmin'], update_data['userRole'],
                update_data['isActive'],
                _hash_password(update_data['password']),
                user_id,
            ))
        else:
            cursor.execute("""
                UPDATE Users
                SET userName=%s, emailAddress=%s, mobile=%s,
                    isSuperAdmin=%s, userRole=%s, isActive=%s,
                    updatedAt=NOW()
                WHERE userID=%s
            """, (
                update_data['userName'], update_data['emailAddress'],
                update_data.get('mobile'),
                update_data['isSuperAdmin'], update_data['userRole'],
                update_data['isActive'],
                user_id,
            ))

        # Replace divisions — deactivate all then re-insert
        cursor.execute(
            "UPDATE User_Divisions SET isActive=0 WHERE userID=%s", (user_id,))
        for did in division_ids:
            cursor.execute("""
                INSERT INTO User_Divisions (userID, divisionID, isActive)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE isActive=1
            """, (user_id, did))

        # Replace customers
        cursor.execute(
            "UPDATE User_Customers SET isActive=0 WHERE userID=%s", (user_id,))
        for cid in customer_ids:
            cursor.execute("""
                INSERT INTO User_Customers (userID, customerID, isActive)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE isActive=1
            """, (user_id, cid))

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close(); conn.close()


def deactivate_user(user_id: int):
    """Soft delete — sets isActive=0."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Users SET isActive=0, updatedAt=NOW() WHERE userID=%s", (user_id,))
    conn.commit()
    cursor.close(); conn.close()


def get_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM Users WHERE emailAddress = %s", (email,))
    return cursor.fetchone()