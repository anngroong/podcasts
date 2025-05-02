from flask import Flask, jsonify
import requests
import feedparser

app = Flask(__name__)

def fetch_latest_episodes(count=3):
    rss_url = "https://feeds.buzzsprout.com/1215113.rss"
    headers = {'User-Agent': 'Mozilla/5.0 (GroongBot)'}
    resp = requests.get(rss_url, headers=headers)
    feed = feedparser.parse(resp.content)

    episodes = []
    for entry in feed.entries[:count]:
        mp3_url = entry.enclosures[0].href if entry.enclosures else "N/A"
        mp3_filename = mp3_url.split("/")[-1] if mp3_url != "N/A" else "N/A"
        duration = entry.get("itunes_duration", "N/A")
        length = entry.enclosures[0].length if entry.enclosures else "N/A"

        episodes.append({
            "title": entry.title,
            "podcast_file": mp3_filename,
            "podcast_duration": duration,
            "podcast_bytes": length
        })

    return episodes

@app.route('/')
def api_endpoint():
    return jsonify(fetch_latest_episodes())

if __name__ == '__main__':
    # Run as script: print to console
    print("Running as script. Fetching latest episodes...\n")
    episodes = fetch_latest_episodes()
    for i, ep in enumerate(episodes, 1):
        print(f"Episode {i}:")
        print(f"  Title       : {ep['title']}")
        print(f"  podcast_file = \"{ep['podcast_file']}\"")
        print(f"  podcast_duration = \"{ep['podcast_duration']}\"")
        print(f"  podcast_bytes = \"{ep['podcast_bytes']}\"")
        print()
    # Optional: run server too
    # app.run(debug=True, port=8080)

