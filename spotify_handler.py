from config import sp

def get_track_info(spotify_url):
    track_id = spotify_url.split('/')[-1].split('?')[0]
    return sp.track(track_id)