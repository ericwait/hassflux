import typer
from typing import Optional
from .migration import run_migration
from .config import settings
from .tools import tools_app

app = typer.Typer(
    name="hassflux",
    help="A tool to migrate Home Assistant sensor data from MariaDB to InfluxDB.",
    add_completion=False,
)
app.add_typer(tools_app, name="tools")

@app.command()
def migrate(
    batch_size: Optional[int] = typer.Option(
        None, 
        "--batch-size", "-b", 
        help="Number of records to process per batch (overrides config)."
    ),
    reset: bool = typer.Option(
        False, 
        "--reset", 
        help="Reset migration progress and start from the beginning."
    ),
):
    """
    Run the migration process.
    """
    effective_batch_size = batch_size or settings.batch_size
    typer.echo(f"Starting migration (batch_size={effective_batch_size}, reset={reset})")
    run_migration(batch_size=effective_batch_size, reset_progress=reset)

@app.command()
def version():
    """
    Show the version of hassflux.
    """
    typer.echo("hassflux v0.1.0")

if __name__ == "__main__":
    app()
