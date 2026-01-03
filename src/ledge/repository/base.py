from abc import ABC, abstractmethod
from ..domain import models


class Repository(ABC):
    """Abstract base class for a repository handling commodities, accounts, and transactions."""

    @abstractmethod
    def add_commodity(self, commodity: models.CommodityCreate) -> models.Commodity:
        """Add a new commodity to the repository."""
        pass

    @abstractmethod
    def get_commodity(
        self, commodity_id: models.CommodityID
    ) -> models.Commodity | None:
        """Retrieve a commodity by its ID."""
        pass

    @abstractmethod
    def open_account(self, account: models.AccountCreate) -> models.Account:
        """Open a new account in the repository."""
        pass

    @abstractmethod
    def get_accounts(self) -> list[models.Account]:
        """Retrieve all accounts from the repository."""
        pass

    @abstractmethod
    def get_account_by_id(self, account_id: models.AccountID) -> models.Account | None:
        """Retrieve an account by its ID."""
        pass

    @abstractmethod
    def set_account_status(self, status: models.AccountStatus) -> None:
        """Set the status of an account."""
        pass

    @abstractmethod
    def get_transactions(
        self, account_id: models.AccountID
    ) -> list[models.Transaction]:
        """Retrieve all transactions for a given account."""
        pass

    @abstractmethod
    def add_transaction(
        self, transaction: models.TransactionCreate
    ) -> models.Transaction:
        """Add a new transaction to the repository."""
        pass
