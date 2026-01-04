import psycopg2
import pytest
from ledge.repository.postgresql import PostgreSQLRepository
from psycopg2 import errorcodes
from ledge.repository.postgresql.schema import SCHEMAS


def error_factory(message: str, pg_code: str):
    """Helper to create a psycopg2.Error with a specific pgcode."""

    class MockError(psycopg2.OperationalError):
        # needed to make factory because pgcode is read-only
        pgcode: str = pg_code

        def __init__(self, msg: str):
            super().__init__(msg)

    return MockError(message)


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("db_name", "test_db")
    monkeypatch.setenv("postgres_user", "user")
    monkeypatch.setenv("postgres_password", "pass")
    monkeypatch.setenv("postgres_host", "localhost")
    monkeypatch.setenv("postgres_port", "5432")


def test_open_success(mocker, mock_env):
    """Test that open() calls psycopg2 with correct env vars."""

    mock_connect = mocker.patch("psycopg2.connect")

    repo = PostgreSQLRepository()
    repo.open()

    mock_connect.assert_called_with(
        dbname="test_db",
        user="user",
        password="pass",
        host="localhost",
        port="5432",
    )
    assert repo._connection is not None


def test_open_auth_failure(mocker, mock_env):
    """Test auth failure raises ConnectionError"""

    mock_connect = mocker.patch("psycopg2.connect")
    # insert error with INVALID_PASSWORD code
    error = error_factory("Fatal error...", errorcodes.INVALID_PASSWORD)
    mock_connect.side_effect = error
    repo = PostgreSQLRepository()

    with pytest.raises(ConnectionError, match="Authentication failed"):
        repo.open()


def test_catchall_and_silent_failure(mocker, mock_env):
    """Test generic error raises ConnectionError"""

    mock_connect = mocker.patch("psycopg2.connect")
    # insert generic error with no pgcode
    error = psycopg2.OperationalError("Some other error")
    mock_connect.side_effect = error
    repo = PostgreSQLRepository()

    with pytest.raises(
        ConnectionError, match="Failed to connect to the PostgreSQL database"
    ):
        repo.open()

    mock_connect.side_effect = None
    mock_connect.return_value = None
    repo = PostgreSQLRepository()
    with pytest.raises(
        ConnectionError, match="Failed to connect to the PostgreSQL database"
    ):
        repo.open()


def test_open_db_not_exist(mocker, mock_env):
    """Test db not exist raises ConnectionError"""

    mock_connect = mocker.patch("psycopg2.connect")
    # insert error with INVALID_CATALOG_NAME code
    error = error_factory("Database does not exist", errorcodes.INVALID_CATALOG_NAME)
    mock_connect.side_effect = error
    repo = PostgreSQLRepository()

    with pytest.raises(ConnectionError, match="Database does not exist"):
        repo.open()


def test_create_success(mocker, mock_env):
    """Test that create() calls psycopg2 with correct env vars and sets up schema."""

    mock_connect = mocker.patch("psycopg2.connect")

    # First connection (to postgres db for CREATE DATABASE)
    mock_admin_conn = mocker.MagicMock()
    mock_admin_cursor = mock_admin_conn.cursor.return_value

    # Second connection (to new db for schema setup via open())
    mock_db_conn = mocker.MagicMock()
    mock_db_cursor = mock_db_conn.cursor.return_value

    mock_connect.side_effect = [mock_admin_conn, mock_db_conn]

    repo = PostgreSQLRepository()
    repo.create()

    # Verify first connection to postgres for CREATE DATABASE
    assert mock_connect.call_args_list[0] == mocker.call(
        dbname="postgres",
        user="user",
        password="pass",
        host="localhost",
        port="5432",
    )
    mock_admin_conn.set_isolation_level.assert_called_with(
        psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
    )
    mock_admin_cursor.execute.assert_called_with("CREATE DATABASE test_db;")
    mock_admin_conn.close.assert_called_once()  # Verify finally block closes connection

    # Verify second connection via open() for schema setup
    assert mock_connect.call_args_list[1] == mocker.call(
        dbname="test_db",
        user="user",
        password="pass",
        host="localhost",
        port="5432",
    )
    mock_db_cursor.execute.assert_called_with(SCHEMAS)
    mock_db_conn.commit.assert_called_once()
    assert repo._connection is mock_db_conn


def test_create_db_exists(mocker, mock_env):
    """Test db exists raises FileExistsError and closes connection in finally."""

    mock_connect = mocker.patch("psycopg2.connect")
    mock_conn = mock_connect.return_value
    # insert error with DUPLICATE_DATABASE code
    error = error_factory("Database already exists", errorcodes.DUPLICATE_DATABASE)
    mock_conn.cursor.return_value.execute.side_effect = error
    repo = PostgreSQLRepository()

    with pytest.raises(FileExistsError, match="Database already exists"):
        repo.create()

    # Verify connection is closed in finally block even on error
    mock_conn.close.assert_called_once()


def test_create_auth_failure(mocker, mock_env):
    """Test auth failure during create raises ConnectionError."""

    mock_connect = mocker.patch("psycopg2.connect")
    error = error_factory("Fatal error...", errorcodes.INVALID_PASSWORD)
    mock_connect.side_effect = error
    repo = PostgreSQLRepository()

    with pytest.raises(ConnectionError, match="Authentication failed"):
        repo.create()


def test_close_connection(mocker, mock_env):
    """Test that close() closes the connection."""

    mock_connect = mocker.patch("psycopg2.connect")
    mock_conn = mock_connect.return_value

    repo = PostgreSQLRepository()
    repo.open()
    repo.close()

    mock_conn.close.assert_called_once()
    assert repo._connection is None
