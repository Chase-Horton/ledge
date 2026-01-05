import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from ..repository.postgresql import PostgreSQLRepository
from ..domain import models

console = Console()

app = typer.Typer(
    help="Tool for managing commodities.",
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
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show commodity IDs"),
) -> None:
    """List all commodities."""
    commodities = ctx.obj.get_commodities()

    if not commodities:
        console.print("[dim]No commodities found.[/dim]")
        return

    table = Table(title="Commodities", show_header=True, header_style="bold cyan")
    if verbose:
        table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Description")

    for commodity in commodities:
        if verbose:
            table.add_row(
                str(commodity.id),
                commodity.name,
                commodity.description or "[dim]None[/dim]",
            )
        else:
            table.add_row(commodity.name, commodity.description or "[dim]None[/dim]")

    console.print(table)


@app.command()
def add(
    ctx: typer.Context,
    name: str = typer.Argument(help="Name of the commodity"),
    prefix: bool = typer.Option(
        False, help="add --prefix if commodity should be prefixed on strings."
    ),
    description: str | None = typer.Option(
        None, help="Optional description of the commodity"
    ),
) -> None:
    """Add a new commodity."""
    print()
    console.print("[bold cyan]New Commodity[/bold cyan]\n")
    if description == "":
        description = None

    # Display commodity details
    prefix_str = "[green]Yes[/green]" if prefix else "[red]No[/red]"
    desc_str = description or "[dim]None[/dim]"

    console.print(f'[bold]Name:[/bold] [green]"{name}"[/green]')
    console.print(f"[bold]Prefix:[/bold] {prefix_str}")
    console.print(f"[bold]Description:[/bold] {desc_str}")

    if Confirm.ask("\nAdd this commodity?", default=True):
        commodity_create = models.CommodityCreate(
            name=name, prefix=prefix, description=description
        )
        ctx.obj.add_commodity(commodity_create)
        console.print("[green]✓[/green] Commodity added successfully!")
    else:
        console.print("[yellow]Cancelled.[/yellow]")


if __name__ == "__main__":
    app()
