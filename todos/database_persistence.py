# pylint: disable=import-error, unused-import, logging-fstring-interpolation

import os
import logging
import psycopg2
from psycopg2 import extras

logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabasePersistence:
    def __init__(self, session):
        if os.environ.get('FLASK_ENV') == 'production':
            self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        else:
            self.conn = psycopg2.connect(dbname='todos')
            self._db_setup()
        self.session = session

    def _db_setup(self):
        self._create_lists_table()
        self._create_todos_table()

    def _create_lists_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                       SELECT COUNT(*)
                       FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'lists';
                           """)
            exists = cursor.fetchone()[0] != 0
            if not exists:
                query = """
                           CREATE TABLE lists(
                           id serial PRIMARY KEY,
                           title text NOT NULL UNIQUE CHECK(LENGTH(title) > 0)
                           )
                        """
                cursor.execute(query)
                logger.info(f"Executing query: {query}")

    def _create_todos_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                       SELECT COUNT(*)
                       FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'todos';
                           """)
            exists = cursor.fetchone()[0] != 0
            if not exists:
                query = """
                           CREATE TABLE lists(
                           id serial PRIMARY KEY,
                           title text NOT NULL CHECK(LENGTH(title) > 0),
                           completed boolean DEFAULT false,
                           list_id int NOT NULL REFERENCES lists(id) ON DELETE CASCADE
                           )
                        """
                cursor.execute(query)
                logger.info(f"Executing query: {query}")

    def find_todo(self, todo_id):
        with self.conn.cursor(cursor_factory=extras.DictCursor) as cur:
            query = "SELECT * FROM todos WHERE id = %s"
            cur.execute(query, (todo_id,))
            logger.info(f"Executing query: {query}, with todo id: {todo_id}")
            row = cur.fetchone()
            return self._make_todo_from_row(row)

    def _todos_in_list(self, list_id):
        with self.conn.cursor(cursor_factory=extras.DictCursor) as cur:
            query = "SELECT * FROM todos WHERE list_id = %s"
            cur.execute(query, (list_id,))
            logger.info(f"Executing query: {query}, with list id: {list_id}")
            rows = cur.fetchall()
            return [self._make_todo_from_row(row) for row in rows]

    def _make_list_from_row(self, row):
        todos = self._todos_in_list(row['id'])
        return {'id': row['id'],
                'title': row['title'],
                'todos': todos}

    def _make_todo_from_row(self, row):
        return {'id': row['id'],
                'title': row['title'],
                'completed': row['completed'],
                'list_id': row['list_id']}


    def find_list(self, list_id):
        with self.conn.cursor(cursor_factory=extras.DictCursor) as cur:
            query = "SELECT * FROM lists WHERE id = %s"
            cur.execute(query, (list_id,))
            logger.info(f"Executing query: {query}, with list_id: {list_id}")
            row = cur.fetchone()
            return self._make_list_from_row(row)

    def all_todos(self):
        return [todo for lst in self.all_lists()
                    for todo in lst['todos']]

    def all_lists(self):
        with self.conn.cursor(cursor_factory=extras.DictCursor) as cur:
            query = "SELECT * FROM lists"
            cur.execute(query)
            logger.info(f"Executing query: {query}")
            rows = cur.fetchall()
            return [self._make_list_from_row(r) for r in rows]

    def create_new_list(self, title):
        with self.conn.cursor() as cur:
            query = "INSERT INTO lists (title) VALUES (%s)"
            cur.execute(query, (title,))
            logger.info(f"Executing query: {query}, with title {title}")
            self.conn.commit()
        self.session.modified = True

    def update_list_name(self, list_id, new_title):
        with self.conn.cursor() as cur:
            query = "UPDATE lists SET title = %s WHERE id = %s"
            cur.execute(query, (new_title, list_id))
            logger.info(f"Executing query: {query}, with list_id: {list_id}" \
                    f" and title: {new_title}")
            self.conn.commit()
        self.session.modified = True

    def delete_list(self, list_id):
        with self.conn.cursor() as cur:
            query = "DELETE FROM lists WHERE id = %s"
            cur.execute(query, (list_id,))
            logger.info(f"Executing query: {query}, with list_id: {list_id}")
            self.conn.commit()
        self.session.modified = True

    def create_new_todo(self, list_id, title):
        with self.conn.cursor() as cur:
            query = "INSERT INTO todos (title, list_id) VALUES (%s, %s)"
            cur.execute(query, (title, list_id))
            logger.info(f"Executing query: {query}, with list_id: {list_id}" \
                    f" and title: {title}")
            self.conn.commit()
        self.session.modified = True

    def delete_todo_from_list(self, todo_id):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
            self.conn.commit()
        self.session.modified = True

    def update_todo_status(self, todo_id, status):
        with self.conn.cursor() as cur:
            query = "UPDATE todos SET completed = %s WHERE id = %s"
            cur.execute(query, (status, todo_id,))
            logger.info(f"Executing query: {query}, with todo_id: {todo_id}")
            self.conn.commit()
        self.session.modified = True

    def mark_all_todos_completed(self, list_id):
        with self.conn.cursor() as cur:
            query = "UPDATE todos SET completed = true WHERE list_id = %s"
            cur.execute(query, (list_id,))
            logger.info(f"Executing query: {query}, with list_id: {list_id}")
            self.conn.commit()
        self.session.modified = True
