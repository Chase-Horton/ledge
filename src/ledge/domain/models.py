from __future__ import annotations
from dataclasses import dataclass
import datetime
import decimal
from enum import Enum
from typing import NewType, Optional

AccountID = NewType("AccountID", int)
#: A unique identifier for an account.(int)
CommodityID = NewType("CommodityID", int)
#: A unique identifier for a commodity.(int)
TransactionID = NewType("TransactionID", int)
#: A unique identifier for a transaction.(int)
SplitID = NewType("SplitID", int)
#: A unique identifier for a split.(int)


class AccountTypeEnum(str, Enum):
    """Enumeration of possible account types.

    Args:
        asset: Represents an asset account.
        liability: Represents a liability account.
        expense: Represents an expense account.
        income: Represents an income account.
        equity: Represents an equity account.
    """

    asset = "asset"
    liability = "liability"
    expense = "expense"
    income = "income"
    equity = "equity"


class AccountStatusEnum(str, Enum):
    """Enumeration of possible account statuses.

    Args:
        open: Indicates the account is open.
        close: Indicates the account is closed.
    """

    open = "open"
    close = "close"


# Commodity
@dataclass(kw_only=True)
class CommodityBase:
    """Base class for commodities.

    Args:
        name (str): The name of the commodity.
        prefix (bool): A boolean indicating if the commodity should be prefixed on amounts.
    """

    name: str
    prefix: bool = False


@dataclass(kw_only=True)
class CommodityCreate(CommodityBase):
    """Used when creating a new commodity (No ID yet)."""

    pass


@dataclass(kw_only=True)
class Commodity(CommodityBase):
    """Represents a commodity with an assigned ID.

    Args:
        id (CommodityID): The unique identifier for the commodity.
    """

    id: CommodityID


# Account
@dataclass(kw_only=True)
class AccountBase:
    """Base class for accounts.

    Args:
        name (str): The name of the account.
        type (AccountTypeEnum): The type of the account.
        commodity (Optional[Commodity]): The associated commodity for the account.
        open (bool): A boolean indicating if the account is open.
    """

    name: str
    type: AccountTypeEnum
    commodity: Optional[Commodity] = None
    open: bool = True


@dataclass(kw_only=True)
class AccountCreate(AccountBase):
    """Used when creating a new account (No ID yet)."""

    pass


@dataclass(kw_only=True)
class Account(AccountBase):
    """Represents an account with an assigned ID.

    Args:
        id (AccountID): The unique identifier for the account.
    """

    id: AccountID


@dataclass(kw_only=True)
class AccountStatus:
    """Represents the status of an account.

    Args:
        account_id (AccountID): The unique identifier for the account.
        date (datetime.datetime): The date of the status change.
        status (AccountStatusEnum): The status of the account.
    """

    account_id: AccountID
    date: datetime.datetime
    status: AccountStatusEnum


# Split
@dataclass(kw_only=True)
class SplitBase:
    """Represents a split in a transaction.

    Args:
        amount (decimal.Decimal): The amount of the split.
        commodity_id (CommodityID): The ID of the commodity associated with the split.
        account_id (AccountID): The ID of the account associated with the split.
    """

    amount: decimal.Decimal
    commodity_id: CommodityID
    account_id: AccountID


@dataclass(kw_only=True)
class SplitCreate(SplitBase):
    """Used when creating a new split (No ID yet)."""

    pass


@dataclass(kw_only=True)
class Split(SplitBase):
    """Represents a split with an assigned ID.

    Args:
        id (SplitID): The unique identifier for the split.
        transaction_id (TransactionID): The ID of the transaction associated with the split.
    """

    id: SplitID
    transaction_id: TransactionID


@dataclass(kw_only=True)
class TransactionBase:
    """Base class for transactions.

    Args:
        date (datetime.datetime): The date of the transaction.
        description (str): A description of the transaction.
        notes (Optional[str]): Additional notes about the transaction.
    """

    date: datetime.datetime
    description: str
    notes: Optional[str] = None


@dataclass(kw_only=True)
class TransactionCreate(TransactionBase):
    """Used when creating a new transaction (No ID yet).

    Args:
        splits (list[SplitCreate]): A list of new splits associated with the transaction.
    """

    splits: list[SplitCreate]


@dataclass(kw_only=True)
class Transaction(TransactionBase):
    """Represents a transaction with an assigned ID.

    Args:
        id (TransactionID): The unique identifier for the transaction.
        splits (list[Split]): A list of splits associated with the transaction.
    """

    id: TransactionID
    splits: list[Split]
