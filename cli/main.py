# cli/main.py
import os
import sys
import typer
from rich.console import Console
from core.spotify_client import *
from core.helpers import *

app = typer.Typer(help="Spotify Explorer CLI")
console = Console()

@app.command()
def explore(
    release_date: str = typer.Option(None, "--release-date", help="Filter by release date (MM-YYYY)"),
    release_year: int = typer.Option(None, "--release-year", help="Filter by release year (YYYY)"),
    release_year_range: str = typer.Option(None, "--release-year-range", help="Filter by release year range (YYYY-YYYY)"),
    
    key: str = typer.Option(None, "--key", help="Filter by musical key"),
    
    mode: str = typer.Option(None, "--mode", help="Filter by musical mode"),
    
    genre: str = typer.Option(None, "--genre", "-g", help="Filter by genre substring"),
    
    artist: str = typer.Option(None, "--artist", "-a", help="Filter by artist name substring"),
    name: str = typer.Option(None, "--name", "-n", help="Filter by song name substring"),
    
    max_tempo: float = typer.Option(None, "--max-tempo", help="Maximum tempo (BPM)"),
    min_tempo: float = typer.Option(None, "--min-tempo", help="Minimum tempo (BPM)"),
    
    max_duration: float = typer.Option(None, "--max-duration", help="Maximum duration (seconds)"),
    min_duration: float = typer.Option(None, "--min-duration", help="Minimum duration (seconds)"),
    
    max_popularity: int = typer.Option(None, "--max-popularity", help="Maximum popularity (0-100)"),
    min_popularity: int = typer.Option(None, "--min-popularity", help="Minimum popularity (0-100)"),
    
    max_energy: float = typer.Option(None, "--max-energy", help="Maximum energy (0-1)"),
    min_energy: float = typer.Option(None, "--min-energy", help="Minimum energy (0-1)"),
    
    max_danceability: float = typer.Option(None, "--max-danceability", help="Maximum danceability (0-1)"),
    min_danceability: float = typer.Option(None, "--min-danceability", help="Minimum danceability (0-1)"),
    
    max_happiness: float = typer.Option(None, "--max-happiness", help="Maximum happiness (0-1)"),
    min_happiness: float = typer.Option(None, "--min-happiness", help="Minimum happiness (0-1)"),
    
    max_acousticness: float = typer.Option(None, "--max-acousticness", help="Maximum acousticness (0-1)"),
    min_acousticness: float = typer.Option(None, "--min-acousticness", help="Minimum acousticness (0-1)"),
    
    max_instrumentalness: float = typer.Option(None, "--max-instrumentalness", help="Maximum instrumentalness (0-1)"),
    min_instrumentalness: float = typer.Option(None, "--min-instrumentalness", help="Minimum instrumentalness (0-1)"),
    
    max_liveness: float = typer.Option(None, "--max-liveness", help="Maximum liveness (0-1)"),
    min_liveness: float = typer.Option(None, "--min-liveness", help="Minimum liveness (0-1)"),
    
    max_speechiness: float = typer.Option(None, "--max-speechiness", help="Maximum speechiness (0-1)"),
    min_speechiness: float = typer.Option(None, "--min-speechiness", help="Minimum speechiness (0-1)"),
    
    max_loudness: float = typer.Option(None, "--max-loudness", help="Maximum loudness (dB)"),
    min_loudness: float = typer.Option(None, "--min-loudness", help="Minimum loudness (dB)")
    ):
    
    """Explore your cached liked songs with various filters.""" 
    songs = read_cached_songs()
    
    filtered = [
        s for s in songs
            if (contains_value(s, "genres", genre)
            and contains_value(s, "release_date", release_date)
            and contains_value(s, "artist", artist)
            and contains_value(s, "name", name)
            and is_release_year(s, "release_year", release_year)
            and is_release_year(s, "release_year_range", release_year_range)
            and contains_value(s["audio_features"], "key", key) 
            and contains_value(s["audio_features"], "mode", mode)
            and in_range(s["audio_features"].get("tempo"), min_tempo, max_tempo)
            and in_range(s["audio_features"].get("duration"), min_duration, max_duration)
            and in_range(s["audio_features"].get("energy"), min_energy, max_energy)
            and in_range(s.get("popularity"), min_popularity, max_popularity)
            and in_range(s["audio_features"].get("danceability"), min_danceability, max_danceability)
            and in_range(s["audio_features"].get("happiness"), min_happiness, max_happiness)
            and in_range(s["audio_features"].get("acousticness"), min_acousticness, max_acousticness)
            and in_range(s["audio_features"].get("instrumentalness"), min_instrumentalness, max_instrumentalness)
            and in_range(s["audio_features"].get("liveness"), min_liveness, max_liveness)
            and in_range(s["audio_features"].get("speechiness"), min_speechiness, max_speechiness)
            and in_range(s["audio_features"].get("loudness"), min_loudness, max_loudness)
            )
    ]

    console.print(f"[green]Found {len(filtered)} songs matching filters[/green]")
    
    for s in filtered:
        artist = s.get("artist") or s.get("artist_name") or "Unknown"
        name = s.get("name") or s.get("track_name") or "Unknown"
        console.print(f"[yellow]{artist}[/yellow] — {name}")
        console.print(f"[blue]{s}[/blue]")
        
    cache_songs(filtered, cache_file="songs_cache")

@app.command()
def fetch_songs(limit: int = typer.Option(100, "--limit", help="Maximum number of songs to fetch")):
    """Fetch and cache your liked songs from Spotify."""
    console.print("[cyan]Fetching liked songs from Spotify...[/cyan]")
    songs = fetch_liked_songs(limit=limit)
    cache_songs(songs)
    console.print(f"[green]Fetched and cached {len(songs)} songs.[/green]")

@app.command()
def test_auth():
    """Quick auth test that prints your username (doesn't fetch songs)."""
    try:
        # use same fallback import logic as above
        from core.spotify_client import get_spotify_client
    except Exception:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.spotify_client import get_spotify_client

    sp = get_spotify_client()
    user = sp.current_user()
    console.print(f"[green]Authenticated as:[/green] {user.get('display_name')} ({user.get('id')})")

@app.command()
def create_playlist(
    name: str = typer.Option("My Filtered Liked Songs", "--name", "-n", help="Name of the new playlist"),
    description: str = typer.Option("A playlist created with Spotify Explorer CLI", "--description", "-d", help="Description of the new playlist")
    ):
    
    """Create a new playlist in your Spotify account."""
    sp = get_spotify_client()
    user = sp.current_user()
    playlist = sp.user_playlist_create(user["id"], name, description=description)
    console.print(f"[green]Created playlist:[/green] {playlist.get('name')} (ID: {playlist.get('id')})")
    
    songs = read_cached_songs("songs_cache")
    songs_ids = [s["id"] for s in songs]
        
    sp.playlist_add_items(playlist["id"], songs_ids, position=None)
    console.print(f"[green]Added {len(songs_ids)} songs to playlist.[/green] {[s["name"] for s in songs]}")

@app.command()
def sort_songs(
    attribute: str = typer.Option(..., "--attribute", "-a", help="Attribute to sort songs by (e.g., 'tempo', 'energy')")
    ):
    """Sort cached songs by a given audio feature attribute."""
    songs = read_cached_songs("songs_cache")
    
    console.print(f"[cyan]Sorting songs by attribute: {attribute}...[/cyan]")
    
    if attribute == "name" or attribute == "artist":
        sorted_songs = natsorted(songs, key=lambda s: s.get(attribute, ""))
    else:
        sorted_songs = natsorted(songs, key=lambda s: s["audio_features"].get(attribute, ""))
        
    console.print(f"[green]Songs sorted by {attribute}:[/green]")
    
    for s in sorted_songs:
        artist = s.get("artist") or "Unknown"
        name = s.get("name") or "Unknown"

        if attribute == "name" or attribute == "artist":
            attr_value = s.get(attribute, "N/A")
        else:
            attr_value = s["audio_features"].get(attribute, "N/A")
        console.print(f"[yellow]{artist}[/yellow] — {name} | {attribute}: {attr_value}")

    cache_songs(sorted_songs, cache_file="songs_cache")

@app.command()
def songs_like_this(
    query_songs: str = typer.Option(None, "--songs", "-s", help="Comma-separated list of song names to base recommendations on or if left empty, uses cached songs"),
    candidate_pool: str = typer.Option(None, "--source", "-r", help="Sources for recommendation candidates: 'liked_songs', 'cache', or a comma-separated list of songs"),
    audio_weight: float = typer.Option(0.7, "--audio-weight", help="Weight for audio features in similarity calculation (0 to 1) - default 0.7"),
    genre_weight: float = typer.Option(0.5, "--genre-weight", help="Weight for genre features in similarity calculation (0 to 1) - default 0.5"),
    similarity_threshold: float = typer.Option(0.7, "--similarity-threshold", "-t", help="Minimum similarity score (0 to 1) to consider a song similar - default 0.7")
    ):
    """Given a list of songs, return a list of songs similar to them based on audio features."""
    
    # Check that the user has provided at least one song
    if query_songs:
        try:
            query_songs = [s.strip() for s in query_songs.split(",")]
            for i in range(len(query_songs)):
                query_songs[i] = find_song_by_name(query_songs[i])
        except Exception as e:
            console.print(f"[red]Error parsing query songs:[/red] {e}")
            return []
    if query_songs == None and candidate_pool == None:
        console.print("[red]Error: You must provide at least one song or candidate pool for recommendation.[/red]")
        return []
    elif query_songs == None:
        query_songs = read_cached_songs("songs_cache")
    
    # Fetch audio features for query songs    
    if candidate_pool == "liked_songs":
        candidate_pool = read_cached_songs()
    elif candidate_pool == "cache":
        candidate_pool = read_cached_songs("songs_cache")
    elif candidate_pool.__contains__(","):
        try:
            candidate_pool = [s.strip() for s in candidate_pool.split(",")]
        except Exception as e:
            console.print(f"[red]Error parsing candidate pool songs:[/red] {e}")
            return []
    else:
        return []
        
    all_genres = get_all_genres(candidate_pool)

    # Create genre vectors
    candidate_pool_genre_vectors = genre_vectors(candidate_pool, all_genres)
    query_songs_genre_vectors = genre_vectors(query_songs, all_genres)
    
    # Create audio feature vectors
    candidate_pool_feature_vectors = audio_feature_vectors(candidate_pool)
    query_songs_feature_vectors = audio_feature_vectors(query_songs)
    
    
    # Final Vectors 
    candidate_pool_final_vectors = np.hstack([
        candidate_pool_genre_vectors * genre_weight,
        candidate_pool_feature_vectors * audio_weight
    ])
    
    
    query_songs_final_vector = np.hstack([
        np.mean(query_songs_genre_vectors * genre_weight, axis=0),
        np.mean(query_songs_feature_vectors * audio_weight, axis=0)
    ])
    
    print(find_song_by_name("Basket Case"))
    print(query_songs_feature_vectors)
    print(query_songs_final_vector)
    
    similar_songs = []
    for i, candidate_vector in enumerate(candidate_pool_final_vectors):
        similarities = 1 - cosine_distance(candidate_vector, query_songs_final_vector)

        if similarities >= similarity_threshold:
            console.print(f"[green]Found similar song:[/green] {candidate_pool[i]['name']} with similarity {similarities}")
            similar_songs.append(candidate_pool[i])

    console.print(f"[green]Total similar songs found: {len(similar_songs)}[/green]")
    cache_songs(similar_songs, cache_file="songs_cache")


if __name__ == "__main__":
    app()
