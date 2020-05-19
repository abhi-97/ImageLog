# python run.py --input Source --output Destination

import glob
import shutil
import os
import argparse
from datetime import datetime, date
import time
import json
import pytz

ap = argparse.ArgumentParser()

ap.add_argument("-i", "--input", required=True,
                help="path to source file")

ap.add_argument("-o", "--output", required=True,
                help="path to output file")

args = vars(ap.parse_args())
src_dir = args["input"]
dst_dir = args["output"]

for pngfile in glob.iglob(os.path.join(src_dir, "*.png")):
    shutil.copy(pngfile, dst_dir)

for jpgfile in glob.iglob(os.path.join(src_dir, "*.jpg")):
    shutil.copy(jpgfile, dst_dir)

cwd = args["input"]
os.chdir(cwd)


def convert_date(timestamp):
    d = datetime.utcfromtimestamp(timestamp)
    formated_date = d.strftime('%d %b %Y')
    return formated_date


today = date.today()
copied = today.strftime("%a %d %B %y")
tz_TX = pytz.timezone('America/Chicago')
datetime_TX = datetime.now(tz_TX)

data = {'files': []}
with os.scandir() as src_dir:
    for entry in src_dir:
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

os.chdir("/Users/abhinntrivedi/Desktop/Code/Logs")
time_script_run = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
with open('{}_data.json'.format(time_script_run), 'w') as outfile:
    json.dump(data, outfile)
