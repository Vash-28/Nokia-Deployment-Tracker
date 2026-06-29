"""
models/opportunity_model.py
All DB functions for the Opportunities flow.
Assumes you have a get_db_connection() helper that returns a mysql.connector connection.
"""
from db import get_db_connection   # adjust import to match your project


# ── Read: list page ───────────────────────────────────────────────────────────

def get_all_opportunities():
    """
    Returns every opportunity joined with customer, account, division.
    Also returns aggregated po_count and product_count per opportunity.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            o.opportunityID,
            o.opportunityName,
            o.opportunityNumber,
            o.startDate,
            o.endDate,
            o.totalValue,
            o.isActive,
            c.customerName,
            a.accountName,
            d.divisionName,
            COUNT(DISTINCT p.poID)              AS po_count,
            COUNT(DISTINCT od.productID)        AS product_count
        FROM Opportunity o
        JOIN Customers   c  ON c.customerID  = o.customerID
        JOIN Accounts    a  ON a.accountID   = c.accountID
        LEFT JOIN Division d ON d.divisionID = o.divisionID
        LEFT JOIN PO     p  ON p.opportunityID = o.opportunityID AND p.isActive = 1
        LEFT JOIN Opportunity_Details od ON od.opportunityID = o.opportunityID
        WHERE o.isActive = 1
        GROUP BY o.opportunityID
        ORDER BY o.createdAt DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_opportunity_stats():
    """
    Returns dict: {total, initialized, ongoing, completed}
    Status is determined by comparing startDate/endDate to today.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            COUNT(*)                                                AS total,
            SUM(startDate > CURDATE())                             AS initialized,
            SUM(startDate <= CURDATE() AND (endDate IS NULL OR endDate >= CURDATE())) AS ongoing,
            SUM(endDate < CURDATE())                               AS completed
        FROM Opportunity
        WHERE isActive = 1
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return {
        'total':       row['total']       or 0,
        'initialized': row['initialized'] or 0,
        'ongoing':     row['ongoing']     or 0,
        'completed':   row['completed']   or 0,
    }


def get_opportunity_pos(opp_id):
    """
    Returns PO drill-down data for a given opportunityID.
    Used by the AJAX endpoint /opportunities/<id>/pos
    Returns list of:
      { poID, pOName, products: [str], opp_qty, po_qty, deployed }
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get POs under this opportunity
    cursor.execute("""
        SELECT p.poID, p.pOName
        FROM PO p
        WHERE p.opportunityID = %s AND p.isActive = 1
        ORDER BY p.createdAt
    """, (opp_id,))
    pos = cursor.fetchall()

    result = []
    for po in pos:
        po_id = po['poID']

        # Get products, opp qty, po qty, deployed for each PO
        cursor.execute("""
            SELECT
                pr.productName,
                od.productQuantity  AS opp_qty,
                pd.productQuantity  AS po_qty,
                COALESCE(pd.poActualQuantity, 0) AS deployed
            FROM PO_Details pd
            JOIN Product pr ON pr.productID = pd.productID
            LEFT JOIN Opportunity_Details od
                ON od.opportunityID = %s AND od.productID = pd.productID
            WHERE pd.poID = %s
        """, (opp_id, po_id))
        details = cursor.fetchall()

        result.append({
            'poID':     po_id,
            'pOName':   po['pOName'],
            'products': [d['productName'] for d in details],
            'opp_qty':  sum(d['opp_qty'] or 0 for d in details),
            'po_qty':   sum(d['po_qty']  or 0 for d in details),
            'deployed': sum(d['deployed'] or 0 for d in details),
        })

    cursor.close()
    conn.close()
    return result


# ── Read: dropdowns ───────────────────────────────────────────────────────────

def get_accounts_for_dropdown():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT accountName FROM Accounts WHERE isActive=1 ORDER BY accountName")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def get_customers_for_filter():
    """All customers for the filter bar on list page."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT customerID, customerName FROM Customers WHERE isActive=1 ORDER BY customerName")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def get_customer_map():
    """
    Returns a dict keyed by accountID (as string for JSON):
      { "1": [{customerID, customerName}, ...], ... }
    Used by the create form to filter customers by selected account.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT accountID, customerID, customerName
        FROM Customers
        WHERE isActive = 1
        ORDER BY customerName
    """)
    rows = cursor.fetchall()
    cursor.close(); conn.close()

    mapping = {}
    for r in rows:
        key = str(r['accountID'])
        mapping.setdefault(key, []).append({
            'customerID':   r['customerID'],
            'customerName': r['customerName'],
        })
    return mapping


def get_opportunities_for_dropdown():
    """
    Lightweight opportunity list for dropdowns and cascades.
    Used by PO create form and milestone init page.
    Returns: [{opportunityID, opportunityName, accountID, customerName, totalValue, startDate, endDate}]
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            o.opportunityID,
            o.opportunityName,
            o.totalValue,
            o.startDate,
            o.endDate,
            c.customerName,
            c.accountID
        FROM Opportunity o
        JOIN Customers c ON c.customerID = o.customerID
        WHERE o.isActive = 1
        ORDER BY o.opportunityName
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_divisions_for_dropdown():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT divisionID, divisionName FROM Division WHERE isActive=1 ORDER BY divisionName")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def get_products_for_dropdown():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT productID, productName, productUOM FROM Product WHERE isActive=1 ORDER BY productName")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


# ── Write: create ─────────────────────────────────────────────────────────────

def create_opportunity(opp_data: dict, details: list):
    """
    Inserts one row into Opportunity and N rows into Opportunity_Details.
    Wrapped in a transaction — both succeed or both roll back.

    opp_data keys:
        opportunityName, opportunityNumber, customerID, divisionID,
        startDate, endDate, totalValue, createdBy

    details is a list of dicts with keys:
        productID, productQuantity, productRate, productTotal
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False

        cursor.execute("""
            INSERT INTO Opportunity
                (opportunityName, opportunityNumber, customerID, divisionID,
                 startDate, endDate, totalValue, createdBy)
            VALUES
                (%(opportunityName)s, %(opportunityNumber)s, %(customerID)s, %(divisionID)s,
                 %(startDate)s, %(endDate)s, %(totalValue)s, %(createdBy)s)
        """, opp_data)

        opp_id = cursor.lastrowid

        for d in details:
            cursor.execute("""
                INSERT INTO Opportunity_Details
                    (opportunityID, productID, productQuantity, productRate, productTotal)
                VALUES
                    (%s, %s, %s, %s, %s)
            """, (opp_id, d['productID'], d['productQuantity'], d['productRate'], d['productTotal']))

        conn.commit()
        return opp_id

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()