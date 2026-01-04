import psycopg2
from typing import Optional, List
from ...domain import models as models
from ..base import AbstractRepository
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import errorcodes
import os
from .schema import SCHEMAS
from ...utils import doc_inherit


class PostgreSQLRepository(AbstractRepository):
    """PostgreSQL implementation of the AbstractRepository."""

    def __init__(self) -> None:
        """Initialize the PostgreSQL repository."""
        self._connection: Optional[psycopg2.extensions.connection] = None

    def open(self) -> None:
        """Open a connection to the PostgreSQL database."""
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("db_name"),
                user=os.getenv("postgres_user"),
                password=os.getenv("postgres_password"),
                host=os.getenv("postgres_host"),
                port=os.getenv("postgres_port"),
            )
        except psycopg2.Error as e:
            if e.pgcode == errorcodes.INVALID_PASSWORD:
                raise ConnectionError(
                    "Authentication failed: Check your username and password."
                ) from e
            elif e.pgcode == errorcodes.INVALID_CATALOG_NAME:
                raise ConnectionError(
                    "Database does not exist: Verify the database name."
                ) from e
                # todo say to run create command? or auto create?
            raise ConnectionError(
                f"Failed to connect to the PostgreSQL database: {e}"
            ) from e
        if conn is None:
            raise ConnectionError("Failed to connect to the PostgreSQL database.")
        self._connection = conn

    def create(self) -> None:
        """Create the PostgreSQL database using necessary schemas."""
        conn = None
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=os.getenv("postgres_user"),
                password=os.getenv("postgres_password"),
                host=os.getenv("postgres_host"),
                port=os.getenv("postgres_port"),
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {os.getenv('db_name')};")
        except psycopg2.Error as e:
            if e.pgcode == errorcodes.INVALID_PASSWORD:
                raise ConnectionError(
                    "Authentication failed: Check your username and password."
                ) from e
            elif e.pgcode == errorcodes.DUPLICATE_DATABASE:
                raise FileExistsError("Database already exists.") from e
            raise ConnectionError(
                f"Failed to create the PostgreSQL database: {e}"
            ) from e
        finally:
            if conn:
                conn.close()
        self.open()
        assert self._connection is not None
        cursor = self._connection.cursor()
        cursor.execute(SCHEMAS)
        self._connection.commit()

    def close(self) -> None:
        """Close the connection to the PostgreSQL database."""
        if self._connection:
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> psycopg2.extensions.connection:
        """Get the current database connection."""
        if self._connection is None:
            raise ConnectionError("Database connection is not open.")
        return self._connection

    @doc_inherit
    def add_commodity(self, commodity: models.CommodityCreate) -> models.Commodity:
        query = """INSERT INTO commodity (name, prefix, description)
                   VALUES (%s, %s, %s) RETURNING id;"""
        cursor = self.connection.cursor()
        cursor.execute(query, (commodity.name, commodity.prefix, commodity.description))
        commodity_id = cursor.fetchone()
        if commodity_id is None:
            raise RuntimeError(
                "Failed to retrieve the ID of the newly inserted commodity."
            )
        self.connection.commit()
        return models.Commodity(
            id=commodity_id[0],
            name=commodity.name,
            prefix=commodity.prefix,
            description=commodity.description,
        )

    @doc_inherit
    def get_commodity(
        self, commodity_id: models.CommodityID
    ) -> models.Commodity | None:
        """Retrieve a commodity by its ID."""

        query = """SELECT id, name, prefix, description
                   FROM commodity WHERE id = %s;"""
        cursor = self.connection.cursor()
        cursor.execute(query, (commodity_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return models.Commodity(
            id=row[0], name=row[1], prefix=row[2], description=row[3]
        )

    @doc_inherit
    def open_account(self, account: models.AccountCreate) -> models.Account:
        status_insert = """INSERT INTO account_statuses (status, date, account_id)
                     VALUES (%s, %s, %s);"""

        account_insert = """INSERT INTO accounts (name, type, open, commodity_id)
                     VALUES (%s, %s, %s, %s) RETURNING id;"""
        cursor = self.connection.cursor()

        cursor.execute(
            account_insert,
            (
                account.name,
                account.type,
                True,
                account.commodity.id if account.commodity else None,
            ),
        )
        account_id = cursor.fetchone()
        if account_id is None:
            raise RuntimeError(
                "Failed to retrieve the ID of the newly inserted account."
            )
        account_id_val = account_id[0]
        cursor.execute(
            status_insert,
            (models.AccountStatusEnum.open, account.open_date, account_id_val),
        )
        self.connection.commit()

        return models.Account(
            id=account_id_val,
            name=account.name,
            type=account.type,
            open=True,
            commodity=account.commodity,
        )

    @doc_inherit
    def get_accounts(self) -> List[models.Account]:
        """Retrieve all accounts from the database, including their associated commodities."""

        # get commodity info as well
        query = """SELECT
    a.id,
    a.name,
    a.type,
    a.open,
    a.commodity_id,
    c.name AS commodity_name,
    c.prefix AS commodity_prefix
FROM accounts a
LEFT JOIN commodity c ON a.commodity_id = c.id;"""
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        accounts = []
        for row in rows:
            accounts.append(
                models.Account(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    open=row[3],
                    commodity=models.Commodity(
                        id=row[4], name=row[5], prefix=row[6], description=None
                    )
                    if row[4] is not None
                    else None,
                )
            )
        return accounts

    @doc_inherit
    def get_account_by_id(self, account_id: models.AccountID) -> models.Account | None:
        query = """SELECT
    a.id,
    a.name,
    a.type,
    a.open,
    a.commodity_id,
    c.name AS commodity_name,
    c.prefix AS commodity_prefix
FROM accounts a
LEFT JOIN commodity c ON a.commodity_id = c.id
WHERE a.id = %s;"""
        cursor = self.connection.cursor()
        cursor.execute(query, (account_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return models.Account(
            id=row[0],
            name=row[1],
            type=row[2],
            open=row[3],
            commodity=models.Commodity(
                id=row[4], name=row[5], prefix=row[6], description=None
            )
            if row[4] is not None
            else None,
        )

    @doc_inherit
    def set_account_status(self, status: models.AccountStatus) -> models.AccountStatus:
        query = """INSERT INTO account_statuses (status, date, account_id)
                   VALUES (%s, %s, %s);"""
        cursor = self.connection.cursor()
        cursor.execute(query, (status.status, status.date, status.account_id))
        self.connection.commit()
        return status

    @doc_inherit
    def get_status_by_account(
        self, account_id: models.AccountID
    ) -> List[models.AccountStatus]:
        query = """SELECT id, status, date, account_id
                   FROM account_statuses WHERE account_id = %s
                   ORDER BY date DESC;"""
        cursor = self.connection.cursor()
        cursor.execute(query, (account_id,))
        rows = cursor.fetchall()
        statuses = []
        for row in rows:
            statuses.append(
                models.AccountStatus(status=row[1], date=row[2], account_id=row[3])
            )
        return statuses

    @doc_inherit
    def get_transactions(
        self, account_id: models.AccountID
    ) -> List[models.Transaction]:
        query = """SELECT
    t.id AS transaction_id,
    t.description,
    t.date,
    s.id AS split_id,
    s.amount,
    s.commodity_id,
    s.account_id
FROM transactions t
JOIN splits s ON t.id = s.transaction_id
WHERE t.id IN (
    SELECT DISTINCT transaction_id
    FROM splits
    WHERE account_id = %s
)
ORDER BY t.date DESC, t.id, s.id;"""
        cursor = self.connection.cursor()
        cursor.execute(query, (account_id,))
        rows = cursor.fetchall()

        # Group splits by transaction
        transactions_dict: dict[int, models.Transaction] = {}
        for row in rows:
            txn_id = row[0]
            if txn_id not in transactions_dict:
                transactions_dict[txn_id] = models.Transaction(
                    id=txn_id, description=row[1], date=row[2], splits=[]
                )
            transactions_dict[txn_id].splits.append(
                models.Split(
                    amount=row[4],
                    commodity_id=row[5],
                    account_id=row[6],
                    transaction_id=txn_id,
                )
            )

        return list(transactions_dict.values())

    @doc_inherit
    def add_transaction(
        self, transaction: models.TransactionCreate
    ) -> models.Transaction:
        query = """INSERT INTO transactions (description, date)
                     VALUES (%s, %s) RETURNING id;"""
        cursor = self.connection.cursor()
        cursor.execute(query, (transaction.description, transaction.date))
        transaction_id = cursor.fetchone()
        if transaction_id is None:
            raise RuntimeError(
                "Failed to retrieve the ID of the newly inserted transaction."
            )
        transaction_id_val = transaction_id[0]
        new_splits = []
        for split in transaction.splits:
            split_query = """INSERT INTO splits (account_id, amount, commodity_id, transaction_id)
                             VALUES (%s, %s, %s, %s);"""
            cursor.execute(
                split_query,
                (
                    split.account_id,
                    split.amount,
                    split.commodity_id,
                    transaction_id_val,
                ),
            )
            new_splits.append(
                models.Split(
                    amount=split.amount,
                    commodity_id=split.commodity_id,
                    account_id=split.account_id,
                    transaction_id=transaction_id_val,
                )
            )
        self.connection.commit()
        return models.Transaction(
            id=transaction_id_val,
            description=transaction.description,
            date=transaction.date,
            splits=new_splits,
        )

    @doc_inherit
    def get_account_by_name(self, account_name: str) -> List[models.Account]:
        query = """SELECT
    a.id,
    a.name,
    a.type,
    a.open,
    a.commodity_id,
    c.name AS commodity_name,
    c.prefix AS commodity_prefix
FROM accounts a
LEFT JOIN commodity c ON a.commodity_id = c.id
WHERE a.name ILIKE %s;"""
        cursor = self.connection.cursor()
        cursor.execute(query, (f"%{account_name}%",))
        rows = cursor.fetchall()
        accounts = []
        for row in rows:
            accounts.append(
                models.Account(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    open=row[3],
                    commodity=models.Commodity(
                        id=row[4], name=row[5], prefix=row[6], description=None
                    )
                    if row[4] is not None
                    else None,
                )
            )
        return accounts
