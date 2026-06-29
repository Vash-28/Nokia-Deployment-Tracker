from db import get_db_connection
from models.base import BaseModel

class PODetails(BaseModel):
    table_name = "PO_Details"
    primary_key = "poDetailid"

    @classmethod
    def get_by_po(cls, po_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT pd.*, p.productName
            FROM PO_Details pd
            JOIN Product p ON pd.productID = p.productID
            WHERE pd.poID = %s
        """, (po_id,))
        return cursor.fetchall()

    @classmethod
    def create(cls, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO PO_Details 
                (poID, productID, productQuantity, poActualQuantity,
                 productRate, productTotal, createdAt, updatedAt)
            VALUES (%s, %s, %s, 0, %s, %s, NOW(), NOW())
        """, (
            data['poID'], data['productID'],
            data['productQuantity'], data['productRate'],
            data['productTotal']
        ))
        conn.commit()
        return cursor.lastrowid