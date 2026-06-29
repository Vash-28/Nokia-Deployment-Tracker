from db import get_db_connection

class OpportunityDetail:

    @staticmethod
    def get_by_opportunity(opp_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT od.*, p.productName
            FROM Opportunity_Details od
            JOIN Product p ON od.productID = p.productID
            WHERE od.opportunityID = %s
            """,
            (opp_id,)
        )
        return cursor.fetchall()
    
    @staticmethod
    def count_by_product(product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(DISTINCT opportunityID) FROM Opportunity_Details WHERE productID = %s",
            (product_id,)
        )
        return cursor.fetchone()[0]