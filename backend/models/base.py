from db import get_db_connection

class BaseModel:

    table_name = ""
    primary_key = None

    @classmethod
    def get_all(cls):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"SELECT * FROM {cls.table_name}")
        return cursor.fetchall()
    


    @classmethod
    def get_by_id(cls, id):

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = f"""
        SELECT *
        FROM {cls.table_name}
        WHERE {cls.primary_key} = %s
        """

        cursor.execute(query, (id,))

        return cursor.fetchone()