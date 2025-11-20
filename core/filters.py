def filter_songs(songs, genre=None, min_energy=0.0, max_energy=1.0):
    filtered = [
        s for s in songs
        if (genre is None or any(genre.lower() in g.lower() for g in s["genres"]))
        and (min_energy <= s["energy"] <= max_energy)
    ]
    return filtered
