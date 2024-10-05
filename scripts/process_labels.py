# Reprocesses an exported Audacity labels file, ready for pasting into Youtube description.

import csv
import datetime

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="filename", default="Labels 1.txt",
                    help="Path to Audacity labels file", metavar="FILE")
args = parser.parse_args()

def print_ts(secs, label, lt):
  ts=str(datetime.timedelta(seconds=key))
  if(lt):
    ts=":".join(ts.split(":")[1:])
  print("  {0} {1}".format(ts, timestamps[key]))

print ("Timestamps:")
timestamps = {}
with open(args.filename) as tsv:
  for line in csv.reader(tsv, dialect="excel-tab"):
    secs=round(float(line[0]))
    timestamps[secs] = line[2]

less_than_3600 = max(timestamps.keys()) < 3600

for key in sorted(timestamps.keys()):
  print_ts(key, timestamps[key], less_than_3600)
