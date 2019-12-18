from imgurpython import ImgurClient


def upload_photo(imagePath):
    client_id = '63b649c82008bf4'
    client_secret = '6650cc6094124cb02846462bddcaa3e769628072'
    access_token = 'e3fad34caf7021955728b9cfd1b1bbb092f891cb'
    refresh_token = 'e601fc841e38a9722315d557e7781873cfa1066c'
    client = ImgurClient(client_id, client_secret, access_token, refresh_token)
    album = None # You can also enter an album ID here
    config = {
    'album': album,
    }

    image = client.upload_from_path(imagePath, config=config, anon=False)
    return image['link']