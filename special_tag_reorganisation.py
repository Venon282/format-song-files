def plexAll(entries: list, exclude_tags: tuple[str, ...] = ('title', 'artist', 'year', 'album')):
    """ 
        Plex do not accept special tags except GENRE
        In that case our GENRE tags are copy under REAL_GENRE
        and all other tags are concatenate under the GENRE tag
    """
    for entry in entries:
        plex(entry['TagsToSet'], exclude_tags)

def plex(metadatas:dict, exclude_tags: tuple[str, ...] = ('title', 'artist', 'year', 'album')):
    values = [
        item
        for key, metadata in metadatas.items()
        if key not in exclude_tags
        for item in (metadata if isinstance(metadata, list) else [metadata])
    ]
    metadatas['real_genre'] = metadatas.get('genre', [])
    metadatas['genre'] = list(dict.fromkeys(values)) 
    
