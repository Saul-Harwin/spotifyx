import requests
import json 
from core.spotify_client import get_spotify_client
import time
from cli.main import console
from natsort import natsorted

def fetch_liked_songs(limit=100):
    sp = get_spotify_client()
    tracks = read_cached_songs()
    start_num_tracks = len(tracks) if tracks else 0
    offset = 0
    batch_num = 0
    while True:
        console.print(f"[cyan]Fetching batch {batch_num}...[/cyan]")
        
        if batch_num % 5 == 0 and batch_num != 0:
            console.print("[orange]Pausing for 20 seconds to avoid rate limits...[/orange]")
            time.sleep(20)
            console.print("[cyan]Resuming...[/cyan]")
        
        try:
            batch = sp.current_user_saved_tracks(limit=40, offset=offset)
        except Exception as e:
            console.print(f"[red]Error fetching liked songs: {e}[/red]")
            break
        
        liked_songs_batch = batch.get("items", [])
        batch_ids = []
        batch_songs = []
        
        if not liked_songs_batch:
            console.print("[cyan]No more songs to fetch.[/cyan]")
            break
        
        cached_songs = read_cached_songs()
        if cached_songs:
            batch_length_before_removing_already_cached = len(liked_songs_batch)
            cached_ids = set(song["id"] for song in cached_songs)  # IDs of cached songs
            liked_songs_batch = [
                song for song in liked_songs_batch
                if song["track"]["id"] not in cached_ids
            ]        
        
        if liked_songs_batch:
            for song in liked_songs_batch:
                track = song["track"]
                batch_ids.append(track["id"])
                batch_songs.append({
                    "id": track["id"],
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "artist_id": track["artists"][0]["id"],
                    "release_date": track["album"]["release_date"],
                    "genres": sp.artist(track["artists"][0]["id"]).get("genres", []),
                    "cover": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                    "audio_features": {
                        "popularity": track["popularity"]
                    },
                })
            
            try:
                analysis = fetch_track_analysis(batch_ids)
            except requests.exceptions.HTTPError as e:
                console.print(f"[red]HTTP error: {e}[/red]")
                break
                
            
            for i in range(len(batch_songs)):
                batch_songs[i]["audio_features"] |= analysis[i]
            
            tracks.extend(batch_songs)
        
            offset += len(liked_songs_batch)
        
            if len(tracks) - start_num_tracks >= limit:
                break
            
            batch_num += 1    
        else:
            console.print("[cyan]All songs in this batch are already cached. Skipping...[/cyan]")    
            offset += batch_length_before_removing_already_cached
            
            if len(tracks) - start_num_tracks >= limit:
                break
            
            batch_num += 1
    
    if not tracks:
        return []
    
    return tracks

def fetch_track_analysis(ids):
    """
    Fetches detailed track analysis from an external API.
    Returns a dictionary with various audio features.
    """

    url = "https://api.reccobeats.com/v1/audio-features"
    payload = {}
    headers = {
    'Accept': 'application/json'
    }
    
    params = {
        "ids": ids
    }


    response = requests.request("GET", url, headers=headers, data=payload, params=params)
    response.raise_for_status()  # Raises HTTPError if not 200-299
    
    data = json.loads(response.text) 
    data = data["content"] 
    
    # rename 'id' -> 'reccobeats_id' to avoid confusion with Spotify ID
    for i in range(len(data)):
        data[i]["reccobeats_id"] = data[i].pop("id")
    
    # Handle missing tracks    
    requested_ids = set(ids)  # all 40
    returned_ids = set([track['href'].split("/")[-1] for track in data]) 
    missing_ids = requested_ids - returned_ids
    
    # Remove some data that isn't needed
    for i in range(len(data)):
        del data[i]["href"]
        del data[i]["reccobeats_id"]
    
    remade_data = []    
    
    offset = 0
    for i in range(len(ids)):
        if ids[i] in missing_ids:
            remade_data.append({
                "acousticness": None,
                "danceability": None,
                "energy": None,
                "instrumentalness": None,
                "key": None,
                "liveness": None,
                "loudness": None,
                "mode": None,
                "speechiness": None,
                "tempo": None,
                "valence": None
            })
            offset += 1
        else:
            remade_data.append(data[i-offset])
    
    return remade_data

def cache_songs(songs, cache_file="liked_songs_cache"):
    try:
        with open(f"./data/{cache_file}.json", "w+", encoding="utf-8") as f:
            json.dump(songs, f, ensure_ascii=False, indent=4)
            console.print(f"[green]Cached {len(songs)} songs to {cache_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error caching songs: {e}[/red]")

def read_cached_songs(cache_file="liked_songs_cache"):
    try:
        with open(f"./data/{cache_file}.json", "a+", encoding="utf-8") as f:
            f.seek(0)
            songs = json.load(f)
            console.print(f"[green]Read {len(songs)} cached songs from {cache_file}[/green]")
            return songs
    except Exception as e:
        console.print(f"[red]Error reading cached songs: {e}[/red]")
        return None

def is_release_year(item, type, value=None):
    """
    Checks if the release year of the item matches the given value.
    If value is None, returns True.
    """
    release_date = item.get("release_date")
    if release_date is None:
        return False

    release_date = release_date.split("-")

    if value is None:
        return True

    if type == "release_year":
        year = int(release_date[1])
        return year == value
    elif type == "release_year_range":
        year = int(release_date[1])
        first = int(value.split("-")[0])
        last = int(value.split("-")[1])
        
        return int(year) >= first and int(year) <= last 

def contains_value(item, key, value=None):
    """
    Checks if `value` is in item[key] (case-insensitive).
    item[key] can be a string or a list of strings.
    If value is None, returns True.
    """
    values = item.get(key) or []

    # Ensure it's a list
    if isinstance(values, str):
        values = [values]

    if value is None:
        return True

    value_lower = value.lower()
    return any(value_lower in v.lower() for v in values)

def in_range(value, min_val, max_val):
    if min_val is None and max_val is None:
        return True
    elif value is None:
        return False
    elif min_val is None:
        return float(value) <= max_val 
    elif max_val is None:
        return float(value) >= min_val
     
def sort_songs_by_attribute(songs, attribute):
    """Sort songs by a given audio feature, safely handling None and missing values."""
    return natsorted(songs, key=lambda s: s.get(attribute, ""))
    
   





