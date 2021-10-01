from imgurpython import ImgurClient


def upload_photo(imagePath):
    client_id = '0000000000000000000000000000000000'
    client_secret = '0000000000000000000000000000000000'
    access_token = '0000000000000000000000000000000000'
    refresh_token = '0000000000000000000000000000000000'
    client = ImgurClient(client_id, client_secret, access_token, refresh_token)
    album = None # You can also enter an album ID here
    config = {
    'album': album,
    }

    image = client.upload_from_path(imagePath, config=config, anon=False)
    return image['link']
