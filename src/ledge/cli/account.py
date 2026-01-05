import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime
from ..repository.postgresql import PostgreSQLRepository
from ..domain import models
from prompt_toolkit.shortcuts import choice

console = Console()

app = typer.Typer(
    help="Tool for managing accounts.",
)


@app.callback()
def main(
    ctx: typer.Context,
    repo_type: str = typer.Option(
        "postgres", envvar="repo", help="Repo type: postgres or sqlite"
    ),
) -> None:
    """We set up the repo here and attach it to the context."""
    if repo_type == "postgres":
        repo = PostgreSQLRepository()
        repo.open()
    else:
        pass

    ctx.obj = repo

    def cleanup() -> None:
        repo.close()

    ctx.call_on_close(cleanup)


@app.command()
def list(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show account IDs"),
) -> None:
    """List all accounts."""
    print()
    accounts = ctx.obj.get_accounts()

    if not accounts:
        console.print("[dim]No accounts found.[/dim]")
        return

    table = Table(title="Accounts", show_header=True, header_style="bold cyan")
    if verbose:
        table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Description")

    for account in accounts:
        if verbose:
            table.add_row(
                str(account.id), account.name, account.description or "[dim]None[/dim]"
            )
        else:
            table.add_row(account.name, account.description or "[dim]None[/dim]")

    console.print(table)


@app.command()
def open(ctx: typer.Context) -> None:
    """A CLI prompt tool to open a new account."""
    print()
    console.print("[bold cyan]Open a New Account[/bold cyan]")
    name = typer.prompt("Account Name")
    description = typer.prompt("Account Description", default="")
    choices = [
        (account_type.value, account_type.name)
        for account_type in models.AccountTypeEnum
    ]
    acct_type = choice("Account Type", options=choices)
    print(acct_type)
    open_date = typer.prompt("Open Date (YYYY-MM-DD)", default="")
    try:
        # parse open_date to datetime or set to None
        if open_date:
            open_date_dt = datetime.strptime(open_date, "%Y-%m-%d")
        account = models.AccountCreate(
            name=name,
            description=description if description else None,
            type=models.AccountTypeEnum(acct_type),
            open_date=open_date_dt,
        )
        new_account = ctx.obj.open_account(account)
        console.print(
            f"[green]Account '{name}' created with ID {new_account.id}.[/green]"
        )
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
