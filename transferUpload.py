# python transferupload.py --input Source --output Logs
# Ensure that you give the path to the source and the Logs file

from init_photo_service import service
import pandas as pd
import pickle
import requests
import os
import pytz
import argparse
import json
from datetime import datetime, date
import time
import glob


# Getting the source file from the user
ap = argparse.ArgumentParser()

ap.add_argument("-i", "--input", required=True,
                help="path to source file")

ap.add_argument("-o", "--output", required=True,
                help="path to log file")

args = vars(ap.parse_args())

source_dir = args["input"]

def convert_date(timestamp):
    d = datetime.utcfromtimestamp(timestamp)
    formated_date = d.strftime('%d %b %Y')
    return formated_date

# Uploading a single image

def upload_image(image_path, upload_file_name, token):
    headers = {
    'Authorization': 'Bearer ' + token.token,
    'Content-type': 'application/octet-stream',
    'X-Goog-Upload-Protocol': 'raw',
    'X-Goog-Upload-File-Name': upload_file_name
    }
    img = open(image_path, 'rb').read()
    response = requests.post(upload_url, data=img, headers=headers)
    #print('\nUpload token: {0}'.format(response.content.decode('utf-8')))
    return response

today = date.today()
copied = today.strftime("%a %d %B %y")
tz_TX = pytz.timezone('America/Chicago')
datetime_TX = datetime.now(tz_TX)


# Fetching all the albums

response = service.albums().list(
    pageSize = 50, 
    excludeNonAppCreatedData = False
).execute()

lstAlbums = response.get('albums')
nextPageToken = response.get('nextPageToken')

while nextPageToken:
    response = service.albums().list(
        pageSize = 50, 
        excludeNonAppCreatedData = False,
        pageToken = nextPageToken
)
    lstAlbums.append(response.get('albums'))
    nextPageToken = response.get('nextPageToken')

df_albums = pd.DataFrame(lstAlbums)


# Checking if an album of today's date exists


def check_album_exist(df, name):
    count = 0 
    for index in small_df['title']:
        if index == name:
            fetched_id = small_df['id'][count]
            return True, fetched_id
        count += 1
    return False, 'none'

small_df = df_albums[['id','title']]
answer, album_id = check_album_exist(small_df, copied) 

if answer == False:
    # Requesting to make new album on today's date
    request_body = {
        'album' : {'title' : copied }
    }
    response_album = service.albums().create(body=request_body).execute()
    # Fetching the id of the album
    album_id = response_album.get('id')

# Uploading the images
tokens = []
upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
token = pickle.load(open('token_photoslibrary_v1.pickle', 'rb'))
cwd = args["input"]
os.chdir(cwd)

# Scanning each and every image and then choosing to upload it
with os.scandir() as source_dir:
    for entry in source_dir:
        image_file = entry.name
        print(image_file)
        response = upload_image(image_file, os.path.basename(image_file), token)
        tokens.append(response.content.decode('utf-8'))

new_media_items = [{'simpleMediaItem': {'uploadToken': tok}} for tok in tokens]

# Requesting it to upload it in a specific album
request_body = {
    'albumId' : album_id,
    'newMediaItems' : new_media_items
}

upload_response = service.mediaItems().batchCreate(body=request_body).execute()

# Making a log file in JSON format
data = {'files': []}
with os.scandir() as source_dir:
    for entry in source_dir:
        info = entry.stat()
        file_stats = os.stat(entry)
        created = time.ctime(os.path.getctime(entry))
        data['files'].append({
            'Name': entry.name,
            'LastModified': convert_date(info.st_mtime),
            'DateCopied': copied,
            'FileSize': file_stats.st_size / (1024 * 1024),
            "ChicagoTime:": datetime_TX.strftime("%H:%M:%S"),
            'DateCreated': created
        })

# Saving the log file
out_dir = args["output"]
os.chdir(out_dir)
time_script_run = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
with open('{}_data.json'.format(time_script_run), 'w') as outfile:
    json.dump(data, outfile)
