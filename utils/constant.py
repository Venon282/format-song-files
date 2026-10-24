METADATA_KEYS = ['Title', 'Artist', 'Album', 'AlbumArtist', 'Year', 'Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade', 'Comment']
METADATA_KEYS_CATEGORIES = ['Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade', 'Comment']

# order importance
PLEX_METADATA_KEYS_MODIF = {
    'RealGenre': ['Genre'],
    'Genre' : ['Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade', 'Comment']
}