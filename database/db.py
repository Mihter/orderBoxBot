import psycopg2 as ps

from database.config import host, user, password, db_name, schema_name


class DataBase:
    def __init__(self):
        self.connection = ps.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
        self.connection.autocommit = True

    # Выполнение SQL-запроса
    def exec_update_query(self, query):

        with self.connection.cursor() as cursor:
            # Выполняем SQL-запрос
            cursor.execute(query)

        # Выполнение SQL-запроса с возвратом данных (для SELECT)

    def exec_query(self, query):
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()