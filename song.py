class Song:
    def __init__(self, id, artist, title, key=''):
        self.id = str(id.encode('utf-8'))
        self.artist = str(artist.encode('utf-8'))
        self.title = str(title.encode('utf-8'))
        self.key = str(key.encode('utf-8'))
        self.url = None

    def __str__(self):
        return "%s - %s" % (self.artist, self.title)

    def add_url(self, url):
        self.url = url
