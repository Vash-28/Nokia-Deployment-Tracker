"""
models/po_model.py
All DB functions for the PO flow.
"""
from db import get_db_connection


# ── Read: list page ───────────────────────────────────────────────────────────

def get_all_pos():
    """
    Returns every PO joined with opportunity, customer, account.
    Also returns aggregated total_qty and total_deployed from PO_Details.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            p.poID,
            p.pOName,
            p.startDate,
            p.endDate,
            p.totalValue,
            o.opportunityID,
            o.opportunityName,
            o.opportunityNumber,
            c.customerName,
            a.accountName,
            a.accountID,
            COALESCE(SUM(pd.productQuantity), 0)    AS total_qty,
            COALESCE(SUM(pd.poActualQuantity), 0)   AS total_deployed
        FROM PO p
        JOIN Opportunity o  ON o.opportunityID = p.opportunityID
        JOIN Customers   c  ON c.customerID    = o.customerID
        JOIN Accounts    a  ON a.accountID     = c.accountID
        LEFT JOIN PO_Details pd ON pd.poID     = p.poID
        WHERE p.isActive = 1
        GROUP BY p.poID
        ORDER BY p.createdAt DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_po_stats():
    """Returns dict: {total, initialized, ongoing, completed}"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            COUNT(*)                                                          AS total,
            SUM(startDate > CURDATE())                                        AS initialized,
            SUM(startDate <= CURDATE() AND (endDate IS NULL OR endDate >= CURDATE())) AS ongoing,
            SUM(endDate < CURDATE())                                          AS completed
        FROM PO
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


def get_po_products(po_id):
    """
    Returns product breakdown for a given PO.
    Used by the AJAX expand-row on the PO list page.
    Returns list of:
      { productID, productName, opp_qty, po_qty, deployed }
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            pr.productID,
            pr.productName,
            pd.productQuantity                              AS po_qty,
            COALESCE(pd.poActualQuantity, 0)               AS deployed,
            COALESCE(od.productQuantity, 0)                AS opp_qty
        FROM PO_Details pd
        JOIN Product pr ON pr.productID = pd.productID
        JOIN PO      p  ON p.poID       = pd.poID
        LEFT JOIN Opportunity_Details od
            ON od.opportunityID = p.opportunityID
            AND od.productID    = pd.productID
        WHERE pd.poID = %s
    """, (po_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ── Read: dropdowns ───────────────────────────────────────────────────────────

def get_opportunities_for_dropdown():
    """
    Returns opportunities for the PO create form select.
    Includes accountID so JS can filter by selected account.
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


def get_products_by_opportunity_for_po(opp_id):
    """
    Returns products that exist in an opportunity's Opportunity_Details.
    Used by the AJAX call when user selects an opportunity on the PO create form.
    Returns: [{productID, productName, productUOM, opp_qty}]
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            p.productID,
            p.productName,
            p.productUOM,
            od.productQuantity AS opp_qty
        FROM Opportunity_Details od
        JOIN Product p ON p.productID = od.productID
        WHERE od.opportunityID = %s
        ORDER BY p.productName
    """, (opp_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ── Write: create ─────────────────────────────────────────────────────────────

def create_po(po_data: dict, details: list):
    """
    Inserts one row into PO and N rows into PO_Details.
    Wrapped in a transaction.

    po_data keys:
        pOName, opportunityID, startDate, endDate,
        totalValue, poRemark, createdBy

    details is a list of dicts with keys:
        productID, productQuantity, productRate, productTotal
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False

        cursor.execute("""
            INSERT INTO PO
                (pOName, opportunityID, startDate, endDate,
                 totalValue, poRemark, createdBy)
            VALUES
                (%(pOName)s, %(opportunityID)s, %(startDate)s, %(endDate)s,
                 %(totalValue)s, %(poRemark)s, %(createdBy)s)
        """, po_data)

        po_id = cursor.lastrowid

        for d in details:
            cursor.execute("""
                INSERT INTO PO_Details
                    (poID, productID, productQuantity, productRate, productTotal, poActualQuantity)
                VALUES
                    (%s, %s, %s, %s, %s, 0)
            """, (po_id, d['productID'], d['productQuantity'], d['productRate'], d['productTotal']))

        conn.commit()
        return po_id

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()