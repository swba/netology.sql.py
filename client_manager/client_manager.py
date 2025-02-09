import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .errors import ClientNotExistsError
from .model import Client
from .types import ContactValues, ClientSearchValues


class ClientManager:
    """Manages client records"""

    def __init__(self, conn: psycopg.Connection):
        self.conn = conn


    def setup(self):
        """(Re-)creates client tables

        Note that this method tries to drop existing tables before
        trying to create new ones, so all existing data (if any) will
        be lost.

        """
        self.drop_tables()
        self.ensure_tables()

    def ensure_tables(self):
        """Softly creates client tables"""
        with self.conn.cursor() as cur:
            # Main client table contains first name, last (family) name
            # and email address.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS client (
                    client_id SERIAL PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100));
                """)

            # Client phone number table contains phone numbers attached
            # to clients. It doesn't have primary key, as it's just not
            # needed here. If we required unique phone numbers, then
            # `phone_number` column itself could be a primary key, but
            # I'm quite sure that such conditions should be implemented
            # on the code level, not on the DB level.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS client_phone_number (
                    client_id INTEGER NOT NULL REFERENCES client(client_id) ON DELETE CASCADE,
                    phone_number VARCHAR(20));
                """)

            self.conn.commit()

    def drop_tables(self):
        """Drops all client tables"""
        with self.conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS client_phone_number;
                DROP TABLE IF EXISTS client;
                """)

            self.conn.commit()


    def add_client(self, values: ContactValues) -> Client:
        """Adds new client to database

        Args:
            values: Client data to be added.

        """
        with self.conn.cursor() as cur:
            # Add the main client record.
            cur.execute(
                """
                INSERT INTO client (first_name, last_name, email)
                    VALUES (%s, %s, %s) RETURNING client_id;
                """,
                (
                    values.get('first_name'),
                    values.get('last_name'),
                    values.get('email')
                ))
            (client_id,) = cur.fetchone()

        # Add client phone numbers, if any.
        self._add_phone_numbers(client_id, values.get('phone_numbers'))

        # Return the newly added client.
        return self.load_client(client_id)

    def load_client(self, client_id: int) -> Client | None:
        """Loads and returns client instance given its ID

        Args:
            client_id: Client ID.

        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            # Fetch base client data as a dict.
            cur.execute(
                'SELECT * FROM client WHERE client_id = %s;',
                (client_id,)
            )
            if data := cur.fetchone():
                client = Client(data)
                # Add client phone numbers.
                client.phone_numbers = self._load_phone_numbers(client_id)
                return client

        return None

    def load_clients(self, client_ids: list[int]) -> dict[int, Client]:
        """Loads and returns client instances given their IDs

        Args:
            client_ids: Client IDs.

        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            # Fetch base clients data as a list of dicts.
            cur.execute(
                'SELECT * FROM client WHERE client_id = ANY(%s);',
                (client_ids,)
            )
            clients = {item['client_id']: Client(item) for item in cur.fetchall()}

            # Fetch all phone numbers at once for performance reasons.
            cur.execute(
                'SELECT * FROM client_phone_number WHERE client_id = ANY(%s);',
                (client_ids,)
            )
            for item in cur.fetchall():
                client_id = item['client_id']
                if client_id in clients:
                    clients[client_id].phone_numbers.append(item['phone_number'])

        return clients

    def update_client(self, client: Client) -> Client | None:
        """Updates client data

        Args:
            client: Client instance to update.

        """
        with self.conn.cursor() as cur:
            # Update base client data.
            cur.execute(
                """
                UPDATE client 
                    SET first_name = %s, last_name = %s, email = %s
                    WHERE client_id = %s
                    RETURNING client_id;
                """,
                (
                    client.first_name,
                    client.last_name,
                    client.email,
                    client.id
                ))

            if cur.fetchone():
                # Update client phone numbers.
                self._set_phone_numbers(client.id, client.phone_numbers)

                # Return updated client.
                return self.load_client(client.id)
            else:
                raise ClientNotExistsError(f'Client with ID={client.id} does not exist')

    def delete_client(self, client_id: int):
        """Deletes client given its ID

        Args:
            client_id: Client ID.

        """
        with self.conn.cursor() as cur:
            cur.execute(
                'DELETE FROM client WHERE client_id = %s;',
                (client_id,))

    def search_clients(self, values: ClientSearchValues) -> dict[int, Client] | None:
        """Searches for clients

        Note that this method uses ILIKE for search, so any placeholder
        values including "%" will work as expected.

        Args:
            values: Values to search clients by.

        """
        if values:
            with self.conn.cursor() as cur:
                # Build a dynamic query to select IDs of clients that
                # match filter values.
                query = sql.SQL('SELECT c.client_id FROM client c ')
                if 'phone_number' in values:
                    query += sql.SQL('JOIN client_phone_number cpn ON c.client_id = cpn.client_id ')
                query += sql.SQL('WHERE ')
                where, params = [], []
                for field, value in values.items():
                    table = 'cpn' if field == 'phone_number' else 'c'
                    where.append(sql.Identifier(table, field) + sql.SQL(' ILIKE %s'))
                    params.append(value)
                query += sql.SQL(' AND ').join(where)

                # Query returns list of client IDs.
                cur.execute(query, params)
                client_ids = [client_id for client_id, in cur.fetchall()]

                return self.load_clients(client_ids)


    def add_phone_number(self, client_id: int, phone_number: str) -> Client:
        """Adds single client phone number

        Args:
            client_id: Client ID.
            phone_number: Phone number to add.

        """
        with self.conn.cursor() as cur:
            cur.execute(
                'INSERT INTO client_phone_number VALUES(%s, %s);',
                (client_id, phone_number))
            self.conn.commit()

        # Return updated client instance.
        return self.load_client(client_id)

    def delete_phone_number(self, client_id: int, phone_number: str) -> Client:
        """Deletes single phone number

        Args:
            client_id: Client ID.
            phone_number: Phone number to delete.

        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM client_phone_number 
                    WHERE client_id = %s AND phone_number = %s;
                """,
                (client_id, phone_number))

        # Return updated client instance.
        return self.load_client(client_id)


    def _add_phone_numbers(self, client_id: int, phone_numbers: list[str]):
        """Adds a bunch of client phone numbers

        Args:
            client_id: Client ID.
            phone_numbers: Phone numbers to add.

        """
        if phone_numbers:
            with self.conn.cursor() as cur:
                for phone_number in phone_numbers:
                    cur.execute(
                        'INSERT INTO client_phone_number VALUES(%s, %s);',
                        (client_id, phone_number))
                self.conn.commit()

    def _load_phone_numbers(self, client_id: int) -> list[str]:
        """Loads and returns client phone numbers

        Args:
            client_id: Client ID.

        """
        with self.conn.cursor() as cur:
            cur.execute(
                'SELECT phone_number FROM client_phone_number WHERE client_id = %s;',
                (client_id,)
            )
            return [num for num, in cur.fetchall()]

    def _set_phone_numbers(self, client_id: int, phone_numbers: list[str]):
        """Replaces client's phone numbers

        Args:
            client_id: Client ID.
            phone_numbers: New set of client phone numbers to replace
                the old ones.

        """
        # Just delete all client's existing phone numbers and then add
        # new ones.
        self._delete_phone_numbers(client_id)
        self._add_phone_numbers(client_id, phone_numbers)

        # Return updated client instance.
        return self.load_client(client_id)

    def _delete_phone_numbers(self, client_id: int):
        """Deletes all client's phone numbers

        Args:
            client_id: Client ID.

        """
        with self.conn.cursor() as cur:
            cur.execute(
                'DELETE FROM client_phone_number WHERE client_id = %s;',
                (client_id,))
