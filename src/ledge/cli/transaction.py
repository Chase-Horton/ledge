import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from datetime import datetime
from decimal import Decimal
import re
from prompt_toolkit.shortcuts import choice
from ..repository.postgresql import PostgreSQLRepository
from ..domain import models

console = Console()

app = typer.Typer(
    help="Tool for adding transactions.",
)


def parse_amount(amount_str: str, commodities: list) -> tuple[Decimal, int] | None:
    """Parse an amount string like '50 USD' or '-10 CAD' into (amount, commodity_id)."""
    commodity_map = {comm.name.upper(): comm for comm in commodities}

    match = re.match(r"^(-?\d+\.?\d*)\s+(\w+)$", amount_str.strip())
    if match:
        amount_part, commodity_part = match.groups()
        commodity = commodity_map.get(commodity_part.upper())
        if commodity:
            return Decimal(amount_part), commodity.id

    match = re.match(r"^(\w+)\s+(-?\d+\.?\d*)$", amount_str.strip())
    if match:
        commodity_part, amount_part = match.groups()
        commodity = commodity_map.get(commodity_part.upper())
        if commodity:
            return Decimal(amount_part), commodity.id

    return None


@app.callback()
def main(
    ctx: typer.Context,
    repo_type: str = typer.Option(
        "postgres", envvar="repo", help="Repo type: postgres or sqlite"
    ),
):
    """We set up the repo here and attach it to the context."""
    if repo_type == "postgres":
        repo = PostgreSQLRepository()
        repo.open()
    else:
        pass

    ctx.obj = repo

    def cleanup():
        repo.close()

    ctx.call_on_close(cleanup)


@app.command()
def add(ctx: typer.Context):
    """A CLI prompt tool to add a new transaction."""
    print()
    console.print("[bold cyan]Add a New Transaction[/bold cyan]\n")

    # Get transaction details
    date_str = typer.prompt(
        "Date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d")
    )
    description = typer.prompt("Description")
    notes = typer.prompt("Notes (optional)", default="")

    try:
        txn_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Error: Invalid date format.[/red]")
        return

    # Get available accounts and commodities
    accounts = ctx.obj.get_accounts()
    commodities = ctx.obj.get_commodities()

    if not accounts:
        console.print("[red]Error: No accounts found. Create an account first.[/red]")
        return
    if not commodities:
        console.print(
            "[red]Error: No commodities found. Create a commodity first.[/red]"
        )
        return

    account_choices = [(acc.id, f"{acc.name} ({acc.type})") for acc in accounts]
    commodity_names = [comm.name for comm in commodities]

    # Collect splits
    splits: list[models.SplitCreate] = []
    console.print(
        "\n[bold]Add splits[/bold] (at least 2 required, amounts must sum to 0)"
    )
    console.print(f"[dim]Available commodities: {', '.join(commodity_names)}[/dim]")

    while True:
        console.print(f"\n[dim]Split #{len(splits) + 1}[/dim]")

        # Select account
        account_id = choice(
            message="Choose an account for this split:", options=account_choices
        )

        if account_id is None:
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Enter amount with commodity
        while True:
            amount_input = typer.prompt("Amount (e.g., '50 USD' or '-10 CAD')")
            parsed = parse_amount(amount_input, commodities)
            if parsed:
                amount, commodity_id = parsed
                break
            else:
                console.print(
                    f"[red]Invalid format. Use '<amount> <commodity>' (e.g., '50 USD'). Available: {', '.join(commodity_names)}[/red]"
                )

        splits.append(
            models.SplitCreate(
                amount=amount,
                commodity_id=models.CommodityID(commodity_id),
                account_id=models.AccountID(account_id),
            )
        )

        # Show running total per commodity
        commodity_map = {comm.id: comm for comm in commodities}
        totals_by_commodity: dict[int, Decimal] = {}
        for s in splits:
            totals_by_commodity[s.commodity_id] = (
                totals_by_commodity.get(s.commodity_id, Decimal(0)) + s.amount
            )

        total_parts = []
        for comm_id, total in totals_by_commodity.items():
            commodity = commodity_map.get(comm_id)
            if commodity and commodity.prefix:
                total_parts.append(f"{commodity.name} {total}")
            else:
                total_parts.append(f"{total} {commodity.name if commodity else '?'}")

        console.print(f"[dim]Running total: {', '.join(total_parts)}[/dim]")

        all_balanced = all(t == 0 for t in totals_by_commodity.values())

        if len(splits) >= 2 and all_balanced:
            if not Confirm.ask("Add another split?", default=False):
                break
        elif len(splits) >= 2:
            console.print("[yellow]Warning: Splits don't balance[/yellow]")
            if not Confirm.ask("Add another split?", default=True):
                break

    # Validate balance per commodity
    commodity_map = {comm.id: comm for comm in commodities}
    totals_by_commodity: dict[int, Decimal] = {}
    for s in splits:
        totals_by_commodity[s.commodity_id] = (
            totals_by_commodity.get(s.commodity_id, Decimal(0)) + s.amount
        )

    unbalanced = {
        comm_id: total for comm_id, total in totals_by_commodity.items() if total != 0
    }
    if unbalanced:
        unbalanced_parts = []
        for comm_id, total in unbalanced.items():
            commodity = commodity_map.get(comm_id)
            if commodity and commodity.prefix:
                unbalanced_parts.append(f"{commodity.name} {total}")
            else:
                unbalanced_parts.append(
                    f"{total} {commodity.name if commodity else '?'}"
                )
        console.print(
            f"[red]Error: Transaction doesn't balance. Unbalanced: {', '.join(unbalanced_parts)}[/red]"
        )
        return

    # Show summary
    console.print("\n[bold cyan]Transaction Summary[/bold cyan]")
    console.print(f"[bold]Date:[/bold] {txn_date.strftime('%Y-%m-%d')}")
    console.print(f"[bold]Description:[/bold] {description}")
    if notes:
        console.print(f"[bold]Notes:[/bold] {notes}")

    split_table = Table(show_header=True, header_style="bold")
    split_table.add_column("Account")
    split_table.add_column("Amount", justify="right")

    account_map = {acc.id: acc.name for acc in accounts}
    commodity_map = {comm.id: comm for comm in commodities}

    from collections import defaultdict

    account_splits = defaultdict(list)
    for split in splits:
        account_splits[split.account_id].append(split)

    def account_sort_key(account_id):
        splits_for_account = account_splits[account_id]
        has_positive = any(s.amount > 0 for s in splits_for_account)
        return (not has_positive, account_map.get(account_id, ""))

    for account_id in sorted(account_splits.keys(), key=account_sort_key):
        splits_for_account = account_splits[account_id]
        sorted_account_splits = sorted(
            splits_for_account,
            key=lambda s: (
                s.amount <= 0,
                (comm.name if (comm := commodity_map.get(s.commodity_id)) else ""),
            ),
        )

        amount_parts = []
        for split in sorted_account_splits:
            commodity = commodity_map.get(split.commodity_id)
            commodity_name = commodity.name if commodity else "?"
            amount_style = "green" if split.amount > 0 else "red"

            if commodity and commodity.prefix:
                amount_str = f"{commodity_name} {split.amount}"
            else:
                amount_str = f"{split.amount} {commodity_name}"

            amount_parts.append(f"[{amount_style}]{amount_str}[/{amount_style}]")

        split_table.add_row(
            account_map.get(account_id, str(account_id)), ", ".join(amount_parts)
        )
    console.print(split_table)

    if Confirm.ask("\nCreate this transaction?", default=True):
        transaction = models.TransactionCreate(
            date=txn_date,
            description=description,
            notes=notes if notes else None,
            splits=splits,
        )
        new_txn = ctx.obj.add_transaction(transaction)
        console.print(f"[green]✓[/green] Transaction created with ID {new_txn.id}!")
    else:
        console.print("[yellow]Cancelled.[/yellow]")
