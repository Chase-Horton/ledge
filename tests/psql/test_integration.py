from datetime import datetime
from decimal import Decimal
import uuid
import pytest
import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from ledge.domain import models
from ledge.repository.postgresql.repo import PostgreSQLRepository

# Mark all tests in this module with 'psql_integration' marker
pytestmark = pytest.mark.integration


@pytest.fixture
def temp_db_config(monkeypatch):
    """Set environment variables for a temporary test database name."""
    random_db_name = f"test_db_{uuid.uuid4().hex[:8]}"

    monkeypatch.setenv("db_name", random_db_name)

    return random_db_name


@pytest.fixture
def cleanup_db(temp_db_config):
    """
    Fixture to ensure the test DB is deleted after the test, even if the test fails.
    """
    yield  # Run the test

    # Connect to postgres default DB and drop the temp DB
    # We need to pull the ADMIN credentials from os.getenv manually here
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("postgres_user"),
            password=os.getenv("postgres_password"),
            host=os.getenv("postgres_host"),
            port=os.getenv("postgres_port"),
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {temp_db_config};")
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to clean up test DB {temp_db_config}: {e}")


def test_lifecycle_create_and_open(temp_db_config, cleanup_db):
    """
    1. Create a brand new random DB.
    2. Verify we can open a connection to it.
    """
    try:
        repo = PostgreSQLRepository()

        # 1. Create
        repo.create()

        # 2. Open
        repo.open()

        # 3. Verify
        assert repo.connection is not None
        assert repo.connection.status == psycopg2.extensions.STATUS_READY
    finally:
        repo.close()
        assert repo._connection is None


def test_add_commodity(temp_db_config, cleanup_db):
    """
    Test adding a commodity to the PostgreSQLRepository.
    1. Add a commodity.
    2. Verify the commodity was added correctly.
    """
    try:
        repo = PostgreSQLRepository()
        repo.create()

        new_commodity = models.CommodityCreate(
            name="USD", prefix=True, description="US Dollar"
        )
        commodity = repo.add_commodity(new_commodity)
        assert commodity.id is not None
        assert commodity.name == new_commodity.name
        assert commodity.prefix == new_commodity.prefix
        assert commodity.description == new_commodity.description

        retrieved_commodity = repo.get_commodity(commodity.id)
        assert retrieved_commodity is not None
        assert retrieved_commodity.id == commodity.id
        assert retrieved_commodity.name == commodity.name
        assert retrieved_commodity.prefix == commodity.prefix
        assert retrieved_commodity.description == commodity.description
    finally:
        repo.close()
        assert repo._connection is None


def create_commodity(repo, name="USD", prefix=True, description="US Dollar"):
    """
    Helper function to create a test commodity.
    After verifying commodity creation works in test_add_commodity.
    """
    new_commodity = models.CommodityCreate(
        name=name, prefix=prefix, description=description
    )
    return repo.add_commodity(new_commodity)


def test_add_account(temp_db_config, cleanup_db):
    """
    Test adding an account to the PostgreSQLRepository.
    1. Add a commodity.
    2. Add an account linked to that commodity.
    3. Verify the account was added correctly.
    4. Verify the initial account status was added correctly.
    5. Add an account without a linked commodity
    """
    try:
        repo = PostgreSQLRepository()
        repo.create()

        # Add a commodity first (required foreign key)
        new_commodity = models.CommodityCreate(
            name="USD", prefix=True, description="US Dollar"
        )
        commodity = repo.add_commodity(new_commodity)

        # Now add an account
        new_account = models.AccountCreate(
            name="assets:cash",
            type=models.AccountTypeEnum.asset,
            open=True,
            commodity=commodity,
            open_date=datetime.now(),
        )
        account = repo.open_account(new_account)
        assert account.id is not None
        assert account.name == new_account.name
        assert account.type == new_account.type
        assert account.open == new_account.open
        assert account.commodity is not None
        assert account.commodity.id == commodity.id

        status = repo.get_status_by_account(account.id)
        assert status is not None
        assert status[0].status == models.AccountStatusEnum.open
        assert len(status) == 1

        # Add an account without a linked commodity
        new_account_no_commodity = models.AccountCreate(
            name="expenses:food",
            type=models.AccountTypeEnum.expense,
            open=True,
            commodity=None,
            open_date=datetime.now(),
        )
        account_no_commodity = repo.open_account(new_account_no_commodity)
        assert account_no_commodity.id is not None
        assert account_no_commodity.name == new_account_no_commodity.name
        assert account_no_commodity.type == new_account_no_commodity.type
        assert account_no_commodity.open == new_account_no_commodity.open
        assert account_no_commodity.commodity is None

    finally:
        repo.close()
        assert repo._connection is None


def create_test_account(
    repo, name="assets:bank", account_type=models.AccountTypeEnum.asset, commodity=None
):
    """
    Helper function to create a test account.
    After verifying account creation works in test_add_account.
    """
    new_account = models.AccountCreate(
        name=name,
        type=account_type,
        open=True,
        commodity=commodity,
        open_date=datetime.now(),
    )
    return repo.open_account(new_account)


def test_get_accounts_various(temp_db_config, cleanup_db):
    """
    Test retrieving accounts from the PostgreSQLRepository.
    1. Add multiple accounts.
    2. Retrieve all accounts and verify they match what was added.
    3. Retrieve accounts by name substring and verify results.
    """
    try:
        repo = PostgreSQLRepository()
        repo.create()

        # Add multiple accounts
        create_test_account(repo, name="assets:bank:checking")
        create_test_account(repo, name="assets:bank:savings")
        create_test_account(
            repo,
            name="liabilities:credit_card",
            account_type=models.AccountTypeEnum.liability,
        )

        # Retrieve all accounts
        accounts = repo.get_accounts()
        assert len(accounts) == 3
        account_names = {acc.name for acc in accounts}
        assert "assets:bank:checking" in account_names
        assert "assets:bank:savings" in account_names
        assert "liabilities:credit_card" in account_names

        # Retrieve accounts by name substring
        bank_accounts = repo.get_account_by_name("bank")
        assert len(bank_accounts) == 2
        bank_account_names = {acc.name for acc in bank_accounts}
        assert "assets:bank:checking" in bank_account_names
        assert "assets:bank:savings" in bank_account_names

    finally:
        repo.close()
        assert repo._connection is None


def test_add_account_status(temp_db_config, cleanup_db):
    """
    Test adding account status entries to the PostgreSQLRepository.
    1. Add an account.
    2. Add multiple status entries for that account.
    3. Verify the status entries were added correctly.
    """
    try:
        repo = PostgreSQLRepository()
        repo.create()

        # Add an account first
        account = create_test_account(repo)

        # Add status entries
        status_open = repo.set_account_status(
            models.AccountStatus(
                account_id=account.id,
                status=models.AccountStatusEnum.open,
                date=datetime(2024, 1, 1),
            )
        )
        status_close = repo.set_account_status(
            models.AccountStatus(
                account_id=account.id,
                status=models.AccountStatusEnum.close,
                date=datetime(2024, 6, 1),
            )
        )
        assert status_open is not None
        assert status_close is not None

        assert status_open.account_id == account.id
        assert status_open.status == models.AccountStatusEnum.open
        assert status_open.date == datetime(2024, 1, 1)

        assert status_close.account_id == account.id
        assert status_close.status == models.AccountStatusEnum.close
        assert status_close.date == datetime(2024, 6, 1)

        # Verify all statuses for the account
        statuses = repo.get_status_by_account(account.id)
        # including the initial open status from account creation
        assert len(statuses) == 3
    finally:
        repo.close()
        assert repo._connection is None


def test_get_account_by_id(temp_db_config, cleanup_db):
    """
    Test retrieving an account by ID from the PostgreSQLRepository.
    1. Add an account.
    2. Retrieve the account by its ID.
    3. Verify the retrieved account matches the added account.
    """
    try:
        repo = PostgreSQLRepository()
        repo.create()

        # Add an account first
        account_added = create_test_account(
            repo,
            name="liabilities:credit_card",
            account_type=models.AccountTypeEnum.liability,
        )

        # Retrieve by ID
        account_retrieved = repo.get_account_by_id(account_added.id)
        assert account_retrieved is not None
        assert account_retrieved.id == account_added.id
        assert account_retrieved.name == account_added.name
        assert account_retrieved.type == account_added.type
        assert account_retrieved.open == account_added.open

        account_not_found = repo.get_account_by_id(models.AccountID(9999))
        assert account_not_found is None
    finally:
        repo.close()
        assert repo._connection is None


def test_get_commodity_not_found(temp_db_config, cleanup_db):
    """
    Test retrieving a non-existent commodity from the PostgreSQLRepository.
    1. Attempt to retrieve a commodity with a random ID.
    2. Verify that None is returned.
    """
    try:
        repo = PostgreSQLRepository()
        repo.create()

        non_existent_id = models.CommodityID(9999)
        commodity = repo.get_commodity(non_existent_id)
        assert commodity is None
    finally:
        repo.close()
        assert repo._connection is None


def create_simple_transaction(
    src_account_id: models.AccountID,
    dest_account_id: models.AccountID,
    description: str,
) -> models.TransactionCreate:
    """
    Helper function to create a sample TransactionCreate object.
    Assumes commodity with ID 1
    """
    splits = [
        models.SplitCreate(
            account_id=src_account_id,
            amount=Decimal("-150.0"),
            commodity_id=models.CommodityID(1),
        ),
        models.SplitCreate(
            account_id=dest_account_id,
            amount=Decimal("150.0"),
            commodity_id=models.CommodityID(1),
        ),
    ]
    return models.TransactionCreate(
        date=datetime(2024, 3, 1), splits=splits, description=description
    )


def create_complex_transaction(
    src_account_id: models.AccountID,
    dest_account_id: models.AccountID,
    description: str,
) -> models.TransactionCreate:
    """
    Helper function to create a more complex TransactionCreate object with commodities involved.
    Assumes commodity with IDs 1 and 2
    """
    splits = [
        models.SplitCreate(
            account_id=src_account_id,
            amount=Decimal("1.0"),
            commodity_id=models.CommodityID(2),
        ),
        models.SplitCreate(
            account_id=dest_account_id,
            amount=Decimal("-1.0"),
            commodity_id=models.CommodityID(2),
        ),
    ]
    txn = create_simple_transaction(src_account_id, dest_account_id, description)
    txn.splits.extend(splits)
    return txn


def test_get_transactions(temp_db_config, cleanup_db):
    """
    Test retrieving transactions for an account from the PostgreSQLRepository.
    1. Add operating commodity
    2. Add accounts.
    3. Add multiple transactions for those accounts.
    4. Retrieve the transactions and verify they match what was added.
    """
    try:
        repo = PostgreSQLRepository()
        repo.create()

        # add commodity
        create_commodity(repo)

        # Add an account first
        account1 = create_test_account(repo, name="assets:checking")
        account2 = create_test_account(repo, name="expense:groceries")
        account3 = create_test_account(repo, name="liabilities:credit_card")

        # Add transactions
        transaction1 = create_simple_transaction(
            account1.id, account2.id, "bought groceries"
        )
        transaction2 = create_simple_transaction(
            account1.id, account2.id, "bought more groceries"
        )
        transaction3 = create_simple_transaction(
            account3.id, account2.id, "bought groceries with credit card"
        )
        repo.add_transaction(transaction1)
        repo.add_transaction(transaction2)
        repo.add_transaction(transaction3)

        # Retrieve transactions
        transactions_checking = repo.get_transactions(account1.id)
        assert len(transactions_checking) == 2
        transactions_groceries = repo.get_transactions(account2.id)
        assert len(transactions_groceries) == 3
        transactions_credit_card = repo.get_transactions(account3.id)
        assert len(transactions_credit_card) == 1

        # Verify transaction details
        for txn in transactions_checking:
            assert txn.description in ["bought groceries", "bought more groceries"]
            assert len(txn.splits) == 2
            split_amounts = [split.amount for split in txn.splits]
            assert Decimal("-150.0") in split_amounts
            assert Decimal("150.0") in split_amounts

    finally:
        repo.close()
        assert repo._connection is None
