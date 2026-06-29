from db import get_db_connection
import json


def get_account_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    stats = {}

    cursor.execute("SELECT COUNT(*) AS cnt FROM Accounts WHERE isActive = 1")
    stats['total_accounts'] = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM Customers WHERE isActive = 1")
    stats['total_customers'] = cursor.fetchone()['cnt']

    # Active = isActive=1 and within date range
    cursor.execute("""
        SELECT COUNT(*) AS cnt FROM Opportunity
        WHERE isActive = 1
          AND startDate <= CURDATE()
          AND (endDate IS NULL OR endDate >= CURDATE())
    """)
    stats['active_opps'] = cursor.fetchone()['cnt']

    cursor.execute("""
        SELECT COALESCE(SUM(pd.productTotal), 0) AS total
        FROM PO_Details pd
        JOIN PO p ON pd.poID = p.poID
        WHERE p.isActive = 1
    """)
    stats['total_po_value'] = cursor.fetchone()['total']

    cursor.close()
    conn.close()
    return stats


def get_all_accounts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.accountID,
            a.accountName,
            a.account_details,
            COUNT(DISTINCT c.customerID) AS customer_count,
            COUNT(DISTINCT o.opportunityID) AS opp_count,
            COALESCE(SUM(pd.productTotal), 0) AS po_value
        FROM Accounts a
        LEFT JOIN Customers c ON c.accountID = a.accountID AND c.isActive = 1
        LEFT JOIN Opportunity o ON o.customerID = c.customerID
        LEFT JOIN PO p ON p.opportunityID = o.opportunityID AND p.isActive = 1
        LEFT JOIN PO_Details pd ON pd.poID = p.poID
        WHERE a.isActive = 1
        GROUP BY a.accountID, a.accountName, a.account_details
        ORDER BY a.accountName
    """)
    accounts = cursor.fetchall()

    # Build opp status JSON per account for mini bar charts
    for acct in accounts:
        if acct['opp_count'] and acct['opp_count'] > 0:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN o.isActive = 1 AND o.startDate > CURDATE() THEN 1 ELSE 0 END) AS upcoming,
                    SUM(CASE WHEN o.isActive = 1 AND o.startDate <= CURDATE() AND (o.endDate IS NULL OR o.endDate >= CURDATE()) THEN 1 ELSE 0 END) AS active,
                    SUM(CASE WHEN o.endDate IS NOT NULL AND o.endDate < CURDATE() THEN 1 ELSE 0 END) AS completed
                FROM Opportunity o
                JOIN Customers c ON o.customerID = c.customerID
                WHERE c.accountID = %s
            """, (acct['accountID'],))
            row = cursor.fetchone()
            acct['opp_status_json'] = json.dumps({
                'upcoming':  int(row['upcoming'] or 0),
                'active':    int(row['active'] or 0),
                'completed': int(row['completed'] or 0)
            })
        else:
            acct['opp_status_json'] = None

        acct['po_value'] = f"{acct['po_value']:,.0f}" if acct['po_value'] else '—'

    cursor.close()
    conn.close()
    return accounts


def get_all_customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            c.customerID,
            c.customerName,
            c.customerDetails,
            a.accountName,
            COUNT(DISTINCT o.opportunityID) AS opp_count,
            COALESCE(SUM(pd.poActualQuantity), 0) AS deployed
        FROM Customers c
        JOIN Accounts a ON c.accountID = a.accountID
        LEFT JOIN Opportunity o ON o.customerID = c.customerID
        LEFT JOIN PO p ON p.opportunityID = o.opportunityID
        LEFT JOIN PO_Details pd ON pd.poID = p.poID
        WHERE c.isActive = 1
        GROUP BY c.customerID, c.customerName, c.customerDetails, a.accountName
        ORDER BY a.accountName, c.customerName
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_all_accounts_for_dropdown():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT accountID, accountName FROM Accounts WHERE isActive = 1 ORDER BY accountName")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def create_account(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False
        cursor.execute("""
            INSERT INTO Accounts (accountName, account_details)
            VALUES (%s, %s)
        """, (data['accountName'], data.get('account_details') or None))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def create_customer(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False
        cursor.execute("""
            INSERT INTO Customers (customerName, accountID, customerDetails)
            VALUES (%s, %s, %s)
        """, (data['customerName'], data['accountID'], data.get('customerDetails') or None))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_customers_for_account(account_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            c.customerID,
            c.customerName,
            COUNT(DISTINCT o.opportunityID) AS opp_count,
            COALESCE(SUM(od.productQuantity), 0) AS opp_qty,
            COALESCE(SUM(pd.poActualQuantity), 0) AS deployed
        FROM Customers c
        LEFT JOIN Opportunity o ON o.customerID = c.customerID
        LEFT JOIN Opportunity_Details od ON od.opportunityID = o.opportunityID
        LEFT JOIN PO p ON p.opportunityID = o.opportunityID
        LEFT JOIN PO_Details pd ON pd.poID = p.poID
        WHERE c.accountID = %s AND c.isActive = 1
        GROUP BY c.customerID, c.customerName
        ORDER BY c.customerName
    """, (account_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # Convert Decimal/float for JSON serialisation
    for r in rows:
        r['opp_qty']  = float(r['opp_qty'])
        r['deployed'] = float(r['deployed'])
    return rows