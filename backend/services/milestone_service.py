from db import get_connection

class MilestoneService:

    @staticmethod
    def get_for_product_po(opportunity_id, product_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all milestone stages that have plans for this opp+product
        cursor.execute("""
            SELECT 
                m.milestoneID,
                m.milestoneName,
                mp.milestonePlansID,
                mp.quarterName,
                mpd.milestonePlanDetailsID,
                mpd.m1Value, mpd.m2Value, mpd.m3Value,
                mp.milestoneStartDate
            FROM Milestone_Plans mp
            JOIN Milestone m ON mp.milestoneID = m.milestoneID
            JOIN Milestone_Plan_Details mpd ON mpd.milestonePlansID = mp.milestonePlansID
            WHERE mp.opportunityID = %s AND mp.productID = %s
            ORDER BY m.milestoneID, mp.milestoneStartDate
        """, (opportunity_id, product_id))
        plans = cursor.fetchall()

        # Get actuals
        cursor.execute("""
            SELECT mr.*
            FROM Milestone_Records mr
            JOIN Milestone_Plan_Details mpd ON mr.planDetailsID = mpd.milestonePlanDetailsID
            JOIN Milestone_Plans mp ON mpd.milestonePlansID = mp.milestonePlansID
            WHERE mp.opportunityID = %s AND mp.productID = %s
        """, (opportunity_id, product_id))
        actuals = cursor.fetchall()

        # Index actuals by planDetailsID
        actuals_map = {}
        for a in actuals:
            pid = a['planDetailsID']
            if pid not in actuals_map:
                actuals_map[pid] = []
            actuals_map[pid].append(a)

        # Group by milestone stage
        stages = {}
        for plan in plans:
            mid = plan['milestoneID']
            if mid not in stages:
                stages[mid] = {
                    'milestoneName': plan['milestoneName'],
                    'totalPlanned': 0,
                    'totalActual': 0,
                    'records': []
                }

            planned = (plan['m1Value'] or 0) + (plan['m2Value'] or 0) + (plan['m3Value'] or 0)
            stages[mid]['totalPlanned'] += planned

            # Monthly records
            for i, (month_key, label) in enumerate([('m1Value','M1'),('m2Value','M2'),('m3Value','M3')], 1):
                planned_qty = plan[month_key] or 0
                plan_details_id = plan['milestonePlanDetailsID']

                # Find matching actual for this month
                month_actuals = [a for a in actuals_map.get(plan_details_id, [])
                                 if a.get('actualMonth') and
                                 str(a['actualMonth']).endswith(f'-0{i}') or
                                 str(a['actualMonth']).endswith(f'-{i:02d}')]

                actual_qty = sum(a['actualQuantity'] for a in month_actuals) if month_actuals else 0
                remark = month_actuals[0]['actualRemark'] if month_actuals else None

                stages[mid]['totalActual'] += actual_qty
                stages[mid]['records'].append({
                    'quarterName': plan['quarterName'],
                    'monthLabel': f"{plan['quarterName']} {label}",
                    'plannedQty': planned_qty,
                    'actualQty': actual_qty,
                    'remark': remark
                })

        return list(stages.values())