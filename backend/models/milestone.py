"""
models/milestone_model.py
All DB functions for milestone init and PO tracking.
"""
from db import get_db_connection
from datetime import date, datetime
import math


# ── Helpers ───────────────────────────────────────────────────────────────────

def _quarter_of_month(month_num: int) -> int:
    """Returns 1-4 for a given month number (1-12)."""
    return math.ceil(month_num / 3)


def _quarter_label(year: int, month_num: int) -> str:
    """Returns e.g. 'Q1-2024' for month 2, year 2024."""
    return f"Q{_quarter_of_month(month_num)}-{year}"


def _quarter_start_end(year: int, quarter: int):
    """Returns (start_date, end_date) for a quarter."""
    start_month = (quarter - 1) * 3 + 1
    end_month   = quarter * 3
    # End of last month in quarter
    if end_month == 3:
        end_day = 31
    elif end_month == 6:
        end_day = 30
    elif end_month == 9:
        end_day = 30
    else:
        end_day = 31
    return (
        date(year, start_month, 1),
        date(year, end_month, end_day),
    )


def _month_position_in_quarter(month_num: int) -> int:
    """Returns 1, 2, or 3 (m1/m2/m3) for a month within its quarter."""
    return ((month_num - 1) % 3) + 1


def _all_quarters_in_range(start: date, end: date) -> list:
    """
    Returns list of (year, quarter, start_date, end_date) tuples
    for every quarter that overlaps with the given date range.
    """
    quarters = []
    y, q = start.year, _quarter_of_month(start.month)
    while True:
        qs, qe = _quarter_start_end(y, q)
        if qs > end:
            break
        quarters.append((y, q, qs, qe))
        q += 1
        if q > 4:
            q = 1
            y += 1
    return quarters


def _all_months_in_range(start: date, end: date) -> list:
    """Returns list of (year, month) tuples from start to end inclusive."""
    months = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


# ── AJAX helpers for milestone init cascade ───────────────────────────────────

def get_pos_for_opportunity(opp_id: int) -> list:
    """
    Returns POs for the given opportunity.
    Includes already_tracked flag (True if ANY Milestone_Plans row exists for this PO).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch POs
    cursor.execute("""
        SELECT poID, pOName, startDate, endDate
        FROM PO
        WHERE opportunityID = %s AND isActive = 1
        ORDER BY createdAt
    """, (opp_id,))
    rows = cursor.fetchall()

    # For each PO check if tracking exists (separate query avoids correlated subquery issues)
    tracked_po_ids = set()
    if rows:
        po_ids = [r['poID'] for r in rows]
        fmt    = ','.join(['%s'] * len(po_ids))
        cursor.execute(f"SELECT DISTINCT poID FROM Milestone_Plans WHERE poID IN ({fmt})", po_ids)
        tracked_po_ids = {r['poID'] for r in cursor.fetchall()}

    cursor.close(); conn.close()

    for r in rows:
        r['startDate']       = str(r['startDate']) if r['startDate'] else None
        r['endDate']         = str(r['endDate'])   if r['endDate']   else None
        r['already_tracked'] = r['poID'] in tracked_po_ids
    return rows


def get_products_for_po_tracking(po_id: int) -> list:
    """
    Returns products in a PO from PO_Details.
    Includes already_tracked flag per product (True if Milestone_Plans exists for po+product).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch products in this PO
    cursor.execute("""
        SELECT pr.productID, pr.productName, pd.productQuantity AS po_qty
        FROM PO_Details pd
        JOIN Product pr ON pr.productID = pd.productID
        WHERE pd.poID = %s
        ORDER BY pr.productName
    """, (po_id,))
    rows = cursor.fetchall()

    # Check which products already have tracking for this PO
    tracked_product_ids = set()
    if rows:
        product_ids = [r['productID'] for r in rows]
        fmt = ','.join(['%s'] * len(product_ids))
        cursor.execute(
            f"SELECT DISTINCT productID FROM Milestone_Plans WHERE poID = %s AND productID IN ({fmt})",
            [po_id] + product_ids
        )
        tracked_product_ids = {r['productID'] for r in cursor.fetchall()}

    cursor.close(); conn.close()

    for r in rows:
        r['already_tracked'] = r['productID'] in tracked_product_ids
    return rows


def check_tracking_exists(po_id: int, product_id: int) -> bool:
    """Returns True if Milestone_Plans already has rows for this po+product."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM Milestone_Plans
        WHERE poID = %s AND productID = %s
    """, (po_id, product_id))
    count = cursor.fetchone()[0]
    cursor.close(); conn.close()
    return count > 0


# ── Create milestone plans ────────────────────────────────────────────────────

def create_milestone_plans(opp_id: int, po_id: int, product_id: int, user_id: int):
    """
    Generates Milestone_Plans + Milestone_Plan_Details for every
    (milestone × quarter) in the PO's date range.

    Plan:
    1. Fetch PO start/end dates
    2. Get all milestones from master Milestone table
    3. For each quarter in range × each milestone → insert Milestone_Plans row
    4. For each Milestone_Plans row → insert Milestone_Plan_Details (m1=0, m2=0, m3=0)
    All wrapped in a single transaction.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch PO dates
    cursor.execute("SELECT startDate, endDate FROM PO WHERE poID = %s", (po_id,))
    po = cursor.fetchone()
    if not po or not po['startDate']:
        raise ValueError("PO has no start date — cannot generate milestone plans.")

    start = po['startDate']
    end   = po['endDate'] or date(start.year + 2, start.month, 1)  # fallback 2yr window

    # All milestone master rows
    cursor.execute("""
        SELECT milestoneID, milestoneName, milestoneType, milestonePriority
        FROM Milestone
        ORDER BY milestonePriority
    """)
    milestones = cursor.fetchall()

    if not milestones:
        raise ValueError("No milestones found in Milestone master table.")

    quarters = _all_quarters_in_range(start, end)

    try:
        conn.autocommit = False

        for (year, quarter, qs, qe) in quarters:
            q_label = f"Q{quarter}-{year}"
            for ms in milestones:
                # Insert Milestone_Plans row
                cursor.execute("""
                    INSERT INTO Milestone_Plans
                        (opportunityID, poID, productID, milestoneID,
                         planType, quarterName, milestoneStartDate, milestoneEndDate, createdBy)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    opp_id, po_id, product_id, ms['milestoneID'],
                    ms['milestoneType'], q_label, qs, qe, user_id
                ))
                plan_id = cursor.lastrowid

                # Insert Milestone_Plan_Details row
                cursor.execute("""
                    INSERT INTO Milestone_Plan_Details
                        (milestonePlansID, m1Value, m2Value, m3Value)
                    VALUES (%s, 0, 0, 0)
                """, (plan_id,))

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# ── Tracking page data ────────────────────────────────────────────────────────

def get_tracking_context(po_id: int, product_id: int) -> dict | None:
    """
    Returns display context for the tracking page header strip.
    Returns None if no tracking exists for this po+product.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            a.accountName,
            c.customerName,
            o.opportunityName,
            o.opportunityNumber,
            p.pOName,
            pr.productName,
            p.startDate,
            p.endDate,
            COALESCE(pd.productQuantity, 0)    AS po_qty,
            COALESCE(pd.poActualQuantity, 0)   AS total_deployed
        FROM PO p
        JOIN Opportunity    o  ON o.opportunityID = p.opportunityID
        JOIN Customers      c  ON c.customerID    = o.customerID
        JOIN Accounts       a  ON a.accountID     = c.accountID
        JOIN PO_Details     pd ON pd.poID = p.poID AND pd.productID = %s
        JOIN Product        pr ON pr.productID    = pd.productID
        WHERE p.poID = %s
        LIMIT 1
    """, (product_id, po_id))
    row = cursor.fetchone()
    cursor.close(); conn.close()
    return row


def get_tracking_months(po_id: int, product_id: int) -> list:
    """
    Returns list of month dicts from PO start→end:
      { value: "2024-01", label: "Jan 2024", has_data: bool }
    has_data = True if any Milestone_Records row exists for that month.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # PO dates
    cursor.execute("SELECT startDate, endDate FROM PO WHERE poID = %s", (po_id,))
    po = cursor.fetchone()
    cursor.close(); conn.close()

    if not po or not po['startDate']:
        return []

    start = po['startDate']
    end   = po['endDate'] or date(start.year + 2, start.month, 1)

    # Months that have saved records
    conn2 = get_db_connection()
    cursor2 = conn2.cursor()
    cursor2.execute("""
        SELECT DISTINCT DATE_FORMAT(mr.actualMonth, '%%Y-%%m') AS ym
        FROM Milestone_Records mr
        JOIN Milestone_Plan_Details mpd ON mpd.milestonePlanDetailsID = mr.planDetailsID
        JOIN Milestone_Plans mp ON mp.milestonePlansID = mpd.milestonePlansID
        WHERE mp.poID = %s AND mp.productID = %s
    """, (po_id, product_id))
    months_with_data = {r[0] for r in cursor2.fetchall()}
    cursor2.close(); conn2.close()

    month_names = ['Jan','Feb','Mar','Apr','May','Jun',
                   'Jul','Aug','Sep','Oct','Nov','Dec']

    result = []
    for (y, m) in _all_months_in_range(start, end):
        val = f"{y}-{m:02d}"
        result.append({
            'value':    val,
            'label':    f"{month_names[m-1]} {y}",
            'has_data': val in months_with_data,
        })
    return result


# ── Save actuals ──────────────────────────────────────────────────────────────

def save_actuals(po_id: int, product_id: int, month_str: str, records: list, user_id: int):
    """
    Upserts Milestone_Records for every milestone row submitted.
    If a record already exists for (planDetailsID, actualMonth), UPDATE it.
    Otherwise INSERT.
    Also updates PO_Details.poActualQuantity for the RFS milestone (last by priority).

    records — list of dicts:
        { milestoneID, planDetailsID, planQty, actualQty, remark }
    """


    year, month_num   = int(month_str[:4]), int(month_str[5:])
    actual_month_date = f"{year}-{month_num:02d}-01"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Which column to update in Milestone_Plan_Details (m1/m2/m3 based on month position)
    m_col = f"m{_month_position_in_quarter(month_num)}Value"

    try:
        conn.autocommit = False

        for rec in records:
            plan_details_id = rec['planDetailsID']
            if not plan_details_id:
                continue
    # ... rest of logic
            milestone_id    = rec['milestoneID']
            plan_qty        = rec['planQty']
            actual_qty      = rec['actualQty']
            remark          = rec.get('remark', '') or ''

            # Update the plan qty in Milestone_Plan_Details for this month slot
            cursor.execute(f"""
                UPDATE Milestone_Plan_Details
                SET {m_col} = %s, updatedAt = NOW()
                WHERE milestonePlanDetailsID = %s
            """, (plan_qty, plan_details_id))

            # Upsert Milestone_Records
            cursor.execute("""
                SELECT milestoneRecordsID FROM Milestone_Records
                WHERE planDetailsID = %s AND actualMonth = %s
            """, (plan_details_id, actual_month_date))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE Milestone_Records
                    SET actualQuantity = %s,
                        planQuantity   = %s,
                        actualRemark   = %s,
                        updatedBy      = %s,
                        updatedAt      = NOW()
                    WHERE milestoneRecordsID = %s
                """, (actual_qty, plan_qty, remark, user_id, existing['milestoneRecordsID']))
            else:
                cursor.execute("""
                    INSERT INTO Milestone_Records
                        (planDetailsID, milestoneID, actualMonth,
                         actualQuantity, planQuantity, actualRemark, createdBy)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (plan_details_id, milestone_id, actual_month_date,
                      actual_qty, plan_qty, remark, user_id))

        # Update poActualQuantity in PO_Details
        # Find the last milestone stage (highest milestonePriority) that has
        # any records for this po+product, then sum all its actuals across all months.
        cursor.execute("""
            SELECT mr.milestoneID, SUM(mr.actualQuantity) AS total
            FROM Milestone_Records mr
            JOIN Milestone_Plan_Details mpd ON mpd.milestonePlanDetailsID = mr.planDetailsID
            JOIN Milestone_Plans mp ON mp.milestonePlansID = mpd.milestonePlansID
            JOIN Milestone ms ON ms.milestoneID = mr.milestoneID
            WHERE mp.poID = %s AND mp.productID = %s
            GROUP BY mr.milestoneID
            ORDER BY ms.milestonePriority DESC
            LIMIT 1
        """, (po_id, product_id))
        rfs_row = cursor.fetchone()
        deployed = float(rfs_row['total']) if rfs_row and rfs_row['total'] else 0

        cursor.execute("""
            UPDATE PO_Details
            SET poActualQuantity = %s, updatedAt = NOW()
            WHERE poID = %s AND productID = %s
        """, (deployed, po_id, product_id))

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_milestone_tracking_data(po_id, product_id, month_str):
    """
    Returns milestone data paired by stage (Nokia type=1 + Customer type=2 side by side).
    month_str: "YYYY-MM"
    """
    from db import get_db_connection
    from datetime import datetime

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Parse month
    month_date = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    quarter = (month_date.month - 1) // 3 + 1
    quarter_name = f"Q{quarter}-{month_date.year}"

    print(f"=== get_milestone_tracking_data called ===")
    print(f"po_id={po_id} ({type(po_id)})")
    print(f"product_id={product_id} ({type(product_id)})")
    print(f"month_str={month_str}")
    print(f"quarter_name={quarter_name}")
    print(f"m_col={['m1Value','m2Value','m3Value'][(month_date.month - ((quarter-1)*3+1))]}")

    # Which slot within the quarter (0=m1, 1=m2, 2=m3)
    q_start_month = (quarter - 1) * 3 + 1
    slot = month_date.month - q_start_month
    m_col = ["m1Value", "m2Value", "m3Value"][slot]

    # Get all milestones ordered by priority then type (Nokia=1 first, Customer=2 second)
    cursor.execute(
        "SELECT * FROM Milestone ORDER BY milestonePriority ASC, milestoneType ASC"
    )
    all_milestones = cursor.fetchall()

    # Get plan details for this po+product+quarter
    cursor.execute(
        f"""
        SELECT
            mp.milestoneID,
            mpd.milestonePlanDetailsID as plan_details_id,
            mpd.{m_col} as plan_qty
        FROM Milestone_Plans mp
        JOIN Milestone_Plan_Details mpd ON mp.milestonePlansID = mpd.milestonePlansID
        WHERE mp.poID = %s AND mp.productID = %s AND mp.quarterName = %s
        """,
        (po_id, product_id, quarter_name)
    )
    plan_rows = {r["milestoneID"]: r for r in cursor.fetchall()}

    

    # Get actuals for this month
    cursor.execute(
        """
        SELECT
            mr.milestoneID,
            mr.actualQuantity as actual_qty,
            mr.planQuantity as plan_qty_recorded,
            mr.actualRemark as actual_remark,
            mr.planDetailsID as plan_details_id
        FROM Milestone_Records mr
        JOIN Milestone_Plan_Details mpd ON mr.planDetailsID = mpd.milestonePlanDetailsID
        JOIN Milestone_Plans mp ON mpd.milestonePlansID = mp.milestonePlansID
        WHERE mp.poID = %s AND mp.productID = %s AND mr.actualMonth = %s
        """,
        (po_id, product_id, month_date)
    )
    actual_rows = {r["milestoneID"]: r for r in cursor.fetchall()}

    print(f"plan_rows={plan_rows}")
    print(f"actual_rows={actual_rows}")

    # Build enriched milestone list
    def enrich(ms):
        mid = ms["milestoneID"]
        plan = plan_rows.get(mid, {})
        actual = actual_rows.get(mid, {})
        return {
            **ms,
            "plan_details_id": plan.get("plan_details_id") or actual.get("plan_details_id"),
            "plan_qty": plan.get("plan_qty") or actual.get("plan_qty_recorded"),
            "actual_qty": actual.get("actual_qty"),
            "actual_remark": actual.get("actual_remark"),
        }

    enriched = [enrich(ms) for ms in all_milestones]

    # Pair Nokia (type=1) and Customer (type=2) by priority
    nokia_ms = [m for m in enriched if m["milestoneType"] == 1]
    customer_ms = [m for m in enriched if m["milestoneType"] == 2]

    # Match by milestonePriority
    nokia_by_priority = {m["milestonePriority"]: m for m in nokia_ms}
    customer_by_priority = {m["milestonePriority"]: m for m in customer_ms}

    # Get unique priorities in order
    all_priorities = sorted(set(
        list(nokia_by_priority.keys()) + list(customer_by_priority.keys())
    ))

    paired = []
    for priority in all_priorities:
        nokia_row = nokia_by_priority.get(priority, {
            "milestoneID": None, "milestoneName": "—",
            "milestoneNickname": None, "milestoneDataID": "—",
            "plan_details_id": None, "plan_qty": None,
            "actual_qty": None, "actual_remark": None,
        })
        customer_row = customer_by_priority.get(priority, {
            "milestoneID": None, "milestoneName": "—",
            "milestoneNickname": None, "milestoneDataID": "—",
            "plan_details_id": None, "plan_qty": None,
            "actual_qty": None, "actual_remark": None,
        })

        # Use Nokia name as the stage name (they share the same stage)
        stage_name = nokia_row.get("milestoneName") or customer_row.get("milestoneName")
        # Strip scope suffix if present (e.g. "Material at Hub (Nokia Scope)" → "Material at Hub")
        for suffix in [" (Nokia Scope)", " (Customer Scope)", " Nokia Scope", " Customer Scope"]:
            stage_name = stage_name.replace(suffix, "")

        paired.append({
            "stage_name": stage_name.strip(),
            "nickname": nokia_row.get("milestoneNickname") or customer_row.get("milestoneNickname"),
            "priority": priority,
            "nokia": nokia_row,
            "customer": customer_row,
        })

    return paired, quarter_name