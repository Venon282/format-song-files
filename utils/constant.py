METADATA_KEYS = ['Title', 'Artist', 'Album', 'AlbumArtist', 'Year', 'Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade', 'Comment']
METADATA_KEYS_CATEGORIES = ['Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade', 'Comment']

METADATA_KEYS_INSERT = ['title', 'artist', 'album', 'album_artist', 'year', 'genre', 'style', 'mood', 'language', 'country', 'decade', 'comment']

# order importance
PLEX_METADATA_KEYS_MODIF = {
    'RealGenre': ['Genre'],
    'Genre' : ['Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade', 'Comment']
}