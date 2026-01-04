from abc import ABC, abstractmethod
from ..domain import models


class AbstractRepository(ABC):
    """Abstract base class for a repository handling commodities, accounts, and transactions."""

    @abstractmethod
    def create(self) -> None:
        """Create the necessary data for a new repository.

        Raises:
            FileExistsError: If the repository already exists.
            ConnectionError: If the connection to the repository fails.
        """

    @abstractmethod
    def open(self) -> None:
        """Open a connection to the repository defined in the configuration.

        Raises:
            ConnectionError: If the connection to the repository fails.
        """

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the repository."""

    @abstractmethod
    def add_commodity(self, commodity: models.CommodityCreate) -> models.Commodity:
        """Add a new commodity to the repository.

        Args:
            commodity (models.CommodityCreate): The commodity to add.

        Returns:
            models.Commodity: The added commodity.

        Raises:
            RuntimeError: If we were unable to add the commodity.
        """

    @abstractmethod
    def get_commodity(
        self, commodity_id: models.CommodityID
    ) -> models.Commodity | None:
        """Retrieve a commodity by its ID.

        Args:
            commodity_id (models.CommodityID): The ID of the commodity to retrieve.

        Returns:
            models.Commodity | None: The commodity with the given ID, or None if not found.
        """

    @abstractmethod
    def open_account(self, account: models.AccountCreate) -> models.Account:
        """Open a new account in the repository. Also creates the associated open status.

        Args:
            account (models.AccountCreate): The account to open.

        Returns:
            models.Account: The opened account.

        Raises:
            RuntimeError: If we were unable to open the account.
        """

    @abstractmethod
    def get_accounts(self) -> list[models.Account]:
        """Retrieve all accounts from the repository.

        Returns:
            list[models.Account]: A list of all accounts.
        """

    @abstractmethod
    def get_account_by_id(self, account_id: models.AccountID) -> models.Account | None:
        """Retrieve an account by its ID.

        Args:
            account_id (models.AccountID): The ID of the account to retrieve.

        Returns:
            models.Account | None: The account with the given ID, or None if not found.
        """

    @abstractmethod
    def get_account_by_name(self, account_name: str) -> list[models.Account]:
        """Retrieve a list of accounts that contain the given name.

        Args:
            account_name (str): The name (or part of the name) of the account to retrieve.

        Returns:
            list[models.Account]: A list of accounts matching the given name.
        """

    @abstractmethod
    def set_account_status(self, status: models.AccountStatus) -> models.AccountStatus:
        """Set the status of an account.

        Args:
            status (models.AccountStatus): The account status to add.

        Returns:
            models.AccountStatus: The added account status.
        """

    @abstractmethod
    def get_status_by_account(
        self, account_id: models.AccountID
    ) -> list[models.AccountStatus]:
        """Retrieve all status entries for a given account.

        Args:
            account_id (models.AccountID): The ID of the account.

        Returns:
            list[models.AccountStatus]: A list of account statuses.
        """

    @abstractmethod
    def get_transactions(
        self, account_id: models.AccountID
    ) -> list[models.Transaction]:
        """Retrieve all transactions for a given account.

        Args:
            account_id (models.AccountID): The ID of the account.

        Returns:
            list[models.Transaction]: A list of transactions.
        """

    @abstractmethod
    def add_transaction(
        self, transaction: models.TransactionCreate
    ) -> models.Transaction:
        """Add a new transaction to the repository.

        Args:
            transaction (models.TransactionCreate): The transaction to add.

        Returns:
            models.Transaction: The added transaction.
        """
