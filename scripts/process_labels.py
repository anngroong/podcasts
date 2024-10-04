# Reprocesses an exported Audacity labels file, ready for pasting into Youtube description.

import csv
import datetime

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="filename", default="Labels 1.txt",
                    help="Path to Audacity labels file", metavar="FILE")
args = parser.parse_args()

print ("Timestamps:")
with open(args.filename) as tsv:
  for line in csv.reader(tsv, dialect="excel-tab"):
    secs=round(float(line[0]))
    timestamp=str(datetime.timedelta(seconds=secs))
    print("  {0} {1}".format(timestamp,line[2]))
