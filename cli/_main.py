import typer
from rich.console import Console
from core.spotify_client import fetch_liked_songs
from core.filters import filter_songs

app = typer.Typer()
console = Console()

@app.command()
def explore(
    genre: str = typer.Option(None, help="Filter by genre substring (e.g. 'pop')"),
    min_energy: float = typer.Option(0.0, help="Minimum song energy (0-1)"),
    max_energy: float = typer.Option(1.0, help="Maximum song energy (0-1)")
):
    """Explore your liked songs with filters."""
    console.print("[bold cyan]Fetching liked songs...[/bold cyan]")
    songs = fetch_liked_songs()
    console.print(f"Loaded {len(songs)} songs from cache or API.")

    filtered = filter_songs(songs, genre=genre, min_energy=min_energy, max_energy=max_energy)

    console.print(f"[bold green]Found {len(filtered)} songs matching filters.[/bold green]")
    for s in filtered:
        console.print(f"[yellow]{s['artist']}[/yellow] - {s['name']} (Energy: {s['energy']:.2f})")

if __name__ == "__main__":
    app()
