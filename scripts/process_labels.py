# Reprocesses an exported Audacity labels file, ready for pasting into Youtube description.

import csv
import datetime

print ("Timestamps:")
with open("Labels 1.txt") as tsv:
  for line in csv.reader(tsv, dialect="excel-tab"):
    secs=round(float(line[0]))
    timestamp=str(datetime.timedelta(seconds=secs))
    print("  {0} {1}".format(timestamp,line[2]))
