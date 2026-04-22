import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.db import init_db
from app.services import (
    add_entry,
    backup_db,
    clear_entries,
    copy_entry_content,
    delete_entry,
    get_entry,
    get_pinned_entries_count,
    get_recent_entries,
    get_tag_counts,
    get_total_entries_count,
    get_type_counts,
    list_entries,
    reset_db,
    restore_db,
    search_entries,
    select_entries,
    set_favorite,
    toggle_favorite,
    update_entry,
)

APP_VERSION = "0.1.0"

app = typer.Typer(
    help=(
        "DevVault is a local CLI vault for commands, snippets, fixes, and notes.\n\n"
        "Use it to save useful commands, debugging fixes, short notes, and tagged references "
        "without scattering random files across your machine."
    )
)
console = Console()


def render_rows(rows, title="Entries"):
    table = Table(title=title)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Tags", style="green")
    table.add_column("Pinned", style="yellow")
    table.add_column("Content", style="white")
    table.add_column("Created", style="blue")
    table.add_column("Updated", style="blue")

    for row in rows:
        table.add_row(
            str(row["id"]),
            row["type"],
            row["tags"] or "-",
            "★" if row["favorite"] else "-",
            row["content"],
            row["created_at"],
            row["updated_at"],
        )

    console.print(table)


@app.command(help="Initialize the SQLite database if it does not already exist.")
def init():
    init_db()
    console.print("[bold green]Database initialized.[/bold green]")


@app.command(help="Add a new entry to the vault.")
def add(
    content: str = typer.Argument(
        ...,
        help="The main content to store. Example: a command, fix note, or snippet title.",
    ),
    type: str = typer.Option(
        "note",
        "--type",
        "-t",
        help="Entry type, such as note, fix, command, or snippet.",
    ),
    tags: str = typer.Option(
        "",
        "--tags",
        help="Comma-separated tags. They will be normalized automatically.",
    ),
):
    add_entry(content, type.strip().lower(), tags)
    console.print("[bold green]Entry added.[/bold green]")


@app.command(help="List entries with optional filters.")
def list(
    tag: str = typer.Option("", "--tag", help="Filter entries by tag."),
    type: str = typer.Option("", "--type", "-t", help="Filter entries by exact type."),
    pins: bool = typer.Option(False, "--pins", help="Only show pinned entries."),
):
    rows = list_entries(tag=tag, entry_type=type, favorites_only=pins)

    title = "All Entries"
    if pins:
        title = "Pinned Entries"
    elif tag and type:
        title = f"Entries: tag={tag}, type={type}"
    elif tag:
        title = f"Entries tagged: {tag}"
    elif type:
        title = f"Entries of type: {type}"

    render_rows(rows, title=title)


@app.command(help="Show the most recently added entries, optionally filtered.")
def recent(
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Maximum number of entries to show.",
    ),
    tag: str = typer.Option("", "--tag", help="Filter recent entries by tag."),
    type: str = typer.Option("", "--type", "-t", help="Filter recent entries by exact type."),
    pins: bool = typer.Option(False, "--pins", help="Only include pinned recent entries."),
):
    rows = get_recent_entries(limit=limit, tag=tag, entry_type=type, favorites_only=pins)

    parts = [f"limit={limit}"]
    if tag:
        parts.append(f"tag={tag}")
    if type:
        parts.append(f"type={type}")
    if pins:
        parts.append("pins=true")

    render_rows(rows, title="Recent Entries (" + ", ".join(parts) + ")")


@app.command(help="Select entries using combined filters at the same time.")
def select(
    query: str = typer.Option(
        "",
        "--query",
        "-q",
        help="Free-text search across content, tags, and type.",
    ),
    tag: str = typer.Option("", "--tag", help="Filter by tag."),
    type: str = typer.Option("", "--type", "-t", help="Filter by exact entry type."),
    pins: bool = typer.Option(False, "--pins", help="Only include pinned entries."),
):
    rows = select_entries(
        query=query,
        tag=tag,
        entry_type=type,
        favorites_only=pins,
    )

    parts = []
    if query:
        parts.append(f"query={query}")
    if tag:
        parts.append(f"tag={tag}")
    if type:
        parts.append(f"type={type}")
    if pins:
        parts.append("pins=true")

    title = "Selected Entries"
    if parts:
        title = "Selected: " + ", ".join(parts)

    render_rows(rows, title=title)


@app.command(help="Show all pinned entries.")
def pins():
    rows = list_entries(favorites_only=True)
    render_rows(rows, title="Pinned Entries")


@app.command(help="Search entries by free text.")
def search(
    query: str = typer.Argument(..., help="Search text to match against content, tags, or type."),
):
    rows = search_entries(query)
    render_rows(rows, title=f"Search: {query}")


@app.command(help="Show a single entry by ID.")
def show(
    entry_id: int = typer.Argument(..., help="The numeric ID of the entry to display."),
):
    row = get_entry(entry_id)
    if not row:
        console.print("[bold red]Entry not found.[/bold red]")
        raise typer.Exit(code=1)

    content = (
        f"[cyan]ID:[/cyan] {row['id']}\n"
        f"[magenta]Type:[/magenta] {row['type']}\n"
        f"[green]Tags:[/green] {row['tags'] or '-'}\n"
        f"[yellow]Pinned:[/yellow] {'★' if row['favorite'] else '-'}\n"
        f"[blue]Created:[/blue] {row['created_at']}\n"
        f"[blue]Updated:[/blue] {row['updated_at']}\n\n"
        f"{row['content']}"
    )
    console.print(Panel(content, title="Entry"))


@app.command(help="Edit an existing entry.")
def edit(
    entry_id: int = typer.Argument(..., help="The numeric ID of the entry to update."),
    content: str = typer.Option("", "--content", help="New content for the entry."),
    type: str = typer.Option("", "--type", "-t", help="New exact type."),
    tags: str = typer.Option("", "--tags", help="New comma-separated tags."),
):
    ok = update_entry(entry_id, content=content, entry_type=type, tags=tags)
    if not ok:
        console.print("[bold red]Entry not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]Entry updated.[/bold green]")


@app.command(help="Delete a single entry by ID after confirmation.")
def delete(
    entry_id: int = typer.Argument(..., help="The numeric ID of the entry to delete."),
):
    confirm = typer.confirm(f"Delete entry {entry_id}?")
    if not confirm:
        console.print("[bold yellow]Delete cancelled.[/bold yellow]")
        raise typer.Exit()

    ok = delete_entry(entry_id)
    if not ok:
        console.print("[bold red]Entry not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]Entry deleted.[/bold green]")


@app.command(help="Pin an entry so it stays easy to find.")
def pin(
    entry_id: int = typer.Argument(..., help="The numeric ID of the entry to pin."),
):
    ok = set_favorite(entry_id, 1)
    if not ok:
        console.print("[bold red]Entry not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]Entry pinned.[/bold green]")


@app.command(help="Remove pin status from an entry.")
def unpin(
    entry_id: int = typer.Argument(..., help="The numeric ID of the entry to unpin."),
):
    ok = set_favorite(entry_id, 0)
    if not ok:
        console.print("[bold red]Entry not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]Entry unpinned.[/bold green]")


@app.command(hidden=True)
def favorite(entry_id: int):
    ok = toggle_favorite(entry_id)
    if not ok:
        console.print("[bold red]Entry not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]Pin toggled.[/bold green]")


@app.command(help="Copy entry content to the system clipboard.")
def copy(
    entry_id: int = typer.Argument(..., help="The numeric ID of the entry to copy."),
):
    ok = copy_entry_content(entry_id)
    if not ok:
        console.print("[bold red]Entry not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]Entry copied to clipboard.[/bold green]")


@app.command(help="Delete entries by filters or wipe all entries.")
def clear(
    all: bool = typer.Option(False, "--all", help="Delete all entries in the vault."),
    tag: str = typer.Option("", "--tag", help="Delete entries matching this tag."),
    type: str = typer.Option("", "--type", "-t", help="Delete entries of this exact type."),
    pins: bool = typer.Option(False, "--pins", help="Delete only pinned entries."),
):
    if all:
        confirm = typer.confirm("Clear ALL entries?")
    else:
        parts = []
        if tag:
            parts.append(f"tag={tag}")
        if type:
            parts.append(f"type={type}")
        if pins:
            parts.append("pins only")

        label = ", ".join(parts) if parts else "no filter"
        confirm = typer.confirm(f"Clear entries matching: {label}?")

    if not confirm:
        console.print("[bold yellow]Clear cancelled.[/bold yellow]")
        raise typer.Exit()

    deleted = clear_entries(tag=tag, entry_type=type, favorites_only=pins, clear_all=all)

    if deleted == 0:
        console.print("[bold yellow]No matching entries deleted.[/bold yellow]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Deleted {deleted} entr{'y' if deleted == 1 else 'ies'}.[/bold green]")


@app.command(help="Create a backup copy of the current database.")
def backup():
    ok, message = backup_db()
    if not ok:
        console.print(f"[bold red]{message}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Backup created:[/bold green] {message}")


@app.command(help="Restore the database from backup after confirmation.")
def restore():
    confirm = typer.confirm("Restore database from backup? This will overwrite current data.")
    if not confirm:
        console.print("[bold yellow]Restore cancelled.[/bold yellow]")
        raise typer.Exit()

    ok, message = restore_db()
    if not ok:
        console.print(f"[bold red]{message}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Database restored from backup:[/bold green] {message}")


@app.command("reset-db", help="Delete and recreate the database file after confirmation.")
def reset_db_command():
    confirm = typer.confirm("Reset database? This will delete ALL current entries.")
    if not confirm:
        console.print("[bold yellow]Reset cancelled.[/bold yellow]")
        raise typer.Exit()

    reset_db()
    console.print("[bold green]Database reset.[/bold green]")


@app.command(help="Show summary statistics for the vault.")
def stats():
    total = get_total_entries_count()
    pinned = get_pinned_entries_count()
    type_counts = get_type_counts()
    tag_counts = get_tag_counts()

    console.print(f"[bold cyan]Total entries:[/bold cyan] {total}")
    console.print(f"[bold yellow]Pinned entries:[/bold yellow] {pinned}")
    console.print()

    type_table = Table(title="Entries by Type")
    type_table.add_column("Type", style="magenta")
    type_table.add_column("Count", style="green")

    for row in type_counts:
        type_table.add_row(row["type"], str(row["count"]))

    console.print(type_table)
    console.print()

    tag_table = Table(title="Top Tags")
    tag_table.add_column("Tag", style="cyan")
    tag_table.add_column("Count", style="green")

    for tag, count in tag_counts[:10]:
        tag_table.add_row(tag, str(count))

    console.print(tag_table)


@app.command(help="Show the installed DevVault version.")
def version():
    console.print(f"dvvault {APP_VERSION}")


def main():
    app()


if __name__ == "__main__":
    main()
