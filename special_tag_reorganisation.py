def plex(entries:list, exclude_tags:list[str]=['title' ,'artist' ,'year' ,'album' ]):
    """ 
    Plex do not accept special tags except GENRE
    In that case our GENRE tags are copy under REAL_GENRE
    and all other tags are concatenate under the GENRE tag
    """
    for entry in entries:
        metadatas = entry['TagsToSet']
        metadatas_values = [item
                            for key, metadata in metadatas.items()
                            if key not in exclude_tags
                            for item in (metadata if isinstance(metadata, list) else [metadata])]
        metadatas['real_genre'] = metadatas['genre']
        metadatas['genre'] = metadatas_values