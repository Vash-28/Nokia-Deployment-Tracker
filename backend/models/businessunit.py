from db import get_db_connection
from models.base import BaseModel

class BusinessUnit(BaseModel):
    table_name = "BusinessUnit"
    primary_key = "businessUnitID"

    @classmethod
    def get_by_product(cls, product_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT bu.*, d.divisionName,
                COUNT(DISTINCT od.opportunityID) as opportunity_count
            FROM BusinessUnit bu
            JOIN Division d ON d.divisionID = bu.divisionID
            LEFT JOIN Opportunity_Details od ON od.productID = bu.productID
            WHERE bu.productID = %s
            GROUP BY bu.businessUnitID
        """, (product_id,))
        return cursor.fetchall()
    
    @staticmethod
    def get_by_division(division_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT bu.*, p.productName
            FROM BusinessUnit bu
            JOIN Product p ON bu.productID = p.productID
            WHERE bu.divisionID = %s AND bu.isActive = 1
            """,
            (division_id,)
        )
        return cursor.fetchall()


    @staticmethod
    def create(division_id, product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO BusinessUnit (divisionID, productID, isActive)
            VALUES (%s, %s, 1)
            """,
            (division_id, product_id)
        )
        conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def delete(business_unit_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM BusinessUnit
            WHERE businessUnitID = %s
            """,
            (business_unit_id,)
        )
        conn.commit()
        return cursor.rowcount
    
    @staticmethod
    def get_by_product_with_opp_count(product_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                bu.businessUnitID,
                d.divisionName,
                d.divisionID,
                COUNT(DISTINCT o.opportunityID) as opportunityCount
            FROM BusinessUnit bu
            JOIN Division d ON bu.divisionID = d.divisionID
            LEFT JOIN Opportunity o ON o.divisionID = d.divisionID
            WHERE bu.productID = %s AND bu.isActive = 1
            GROUP BY bu.businessUnitID, d.divisionName, d.divisionID
            """,
            (product_id,)
        )
        return cursor.fetchall()