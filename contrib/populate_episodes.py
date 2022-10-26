import csv
import re
import sys

from datetime import datetime

TEXT="""
+++

title = "{title}"
date = {date}
draft = false
explicit = "no"

aliases = ["/{episode}"]
author = "Armenian News Network - Groong"
episode = "{episode}"
episode_image = "img/episode/default.jpg"
episode_banner = "img/episode/default-banner.jpg"
guests = [{guests}]
images = ["img/episode/default-social.jpg"]
podcast_duration = "{duration}"
podcast_bytes = {bytes}
podcast_file = "{mp3}"
youtube = "{youtube}"
truncate = ""
categories = ["{category}"]
upcoming = false
Description = \"\"\"{description}
\"\"\"

+++

Show Notes

"""

def main():
    with open('groong.csv') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        next(csvreader, None)  # skip the headers
        for row in csvreader:
            filename = re.sub("^[0-9]+", row[6], re.sub(".mp3$", ".md", row[8]))
	    dt = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').isoformat()
            title = re.sub('"', '\\"', row[2])
            with open("output/" + filename, 'a') as output:
                output.write(TEXT.format(date=dt, category=row[1], title=title,
                    description=row[3], youtube=row[4], episode=row[6],
                    guests=row[7], mp3=row[8], bytes=row[9], duration=row[11]))


if __name__ == '__main__':
    sys.exit(main())

