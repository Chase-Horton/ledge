import typer
from . import commodity
from . import account
from . import transaction

app = typer.Typer(
    help="A lightweight ledger CLI application.",
    add_completion=False,
)

app.add_typer(commodity.app, name="commodity")
app.add_typer(account.app, name="account")
app.add_typer(transaction.app, name="transaction")

if __name__ == "__main__":
    app()
