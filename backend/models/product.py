from db import get_db_connection


def get_product_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    stats = {}

    cursor.execute("SELECT COUNT(*) AS cnt FROM Product WHERE isActive = 1")
    stats['total_products'] = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM Division WHERE isActive = 1")
    stats['total_divisions'] = cursor.fetchone()['cnt']

    # Products that appear in at least one active opportunity
    cursor.execute("""
        SELECT COUNT(DISTINCT od.productID) AS cnt
        FROM Opportunity_Details od
        JOIN Opportunity o ON od.opportunityID = o.opportunityID
        WHERE o.isActive = 1
    """)
    stats['in_active_opps'] = cursor.fetchone()['cnt']

    cursor.execute("""
        SELECT COALESCE(SUM(poActualQuantity), 0) AS total FROM PO_Details
    """)
    stats['total_deployed'] = cursor.fetchone()['total']

    cursor.close()
    conn.close()
    return stats


def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Division linked via BusinessUnit
    cursor.execute("""
        SELECT
            p.productID,
            p.productName,
            p.productUOM,
            p.productHSN,
            GROUP_CONCAT(DISTINCT d.divisionName ORDER BY d.divisionName SEPARATOR ', ') AS divisions,
            COUNT(DISTINCT od.opportunityID) AS opp_count,
            COALESCE(SUM(DISTINCT od.productQuantity), 0) AS total_qty,
            COALESCE(SUM(pd.poActualQuantity), 0) AS deployed
        FROM Product p
        LEFT JOIN BusinessUnit bu ON bu.productID = p.productID AND bu.isActive = 1
        LEFT JOIN Division d ON d.divisionID = bu.divisionID AND d.isActive = 1
        LEFT JOIN Opportunity_Details od ON od.productID = p.productID
        LEFT JOIN PO_Details pd ON pd.productID = p.productID
        WHERE p.isActive = 1
        GROUP BY p.productID, p.productName, p.productUOM, p.productHSN
        ORDER BY p.productName
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_divisions_for_dropdown():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT divisionID, divisionName FROM Division WHERE isActive = 1 ORDER BY divisionName")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def create_product(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False
        cursor.execute("""
            INSERT INTO Product (productName, productUOM, productHSN)
            VALUES (%s, %s, %s)
        """, (
            data['productName'],
            data.get('productUOM') or None,
            data.get('productHSN') or None
        ))
        product_id = cursor.lastrowid

        # Link to division via BusinessUnit
        if data.get('divisionID'):
            cursor.execute("""
                INSERT INTO BusinessUnit (productID, divisionID)
                VALUES (%s, %s)
            """, (product_id, data['divisionID']))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()