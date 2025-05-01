# Print out information about the last 3 Groong episodes from the RSS feed.

import feedparser

# RSS feed URL
rss_url = "https://feeds.buzzsprout.com/1215113.rss"

# Parse the feed
feed = feedparser.parse(rss_url)

# Extract data from the 3 latest episodes
latest_episodes = feed.entries[:3]
for i, entry in enumerate(latest_episodes, start=1):
    title = entry.title
    mp3_url = entry.enclosures[0].href if entry.enclosures else "N/A"
    mp3_filename = mp3_url.split("/")[-1] if mp3_url != "N/A" else "N/A"
    duration = entry.get("itunes_duration", "N/A")
    length = entry.enclosures[0].length if entry.enclosures else "N/A"

    print(f"Title       : {title}\n")
    print(f"  podcast_file = \"{mp3_filename}\"")
    print(f"  podcast_duration = \"{duration}\"")
    print(f"  podcast_bytes = \"{length}\"")
    print()

