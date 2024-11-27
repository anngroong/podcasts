# Script that lists guests of the podcast and the last time they appeared.

import os
import re
from datetime import datetime, timedelta
import argparse
import json

def extract_fields(file_content):
    """Extract the 'date', 'guests', 'series', and 'episode' fields from the file content."""
    date_pattern = r"(?i)date\s*=\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    guests_pattern = r"(?i)guests\s*=\s*\[([^\]]+)\]"
    series_pattern = r"(?i)series\s*=\s*\[([^\]]+)\]"
    episode_pattern = r"(?i)episode\s*=\s*\"?(\d+)\"?"
    
    date_match = re.search(date_pattern, file_content)
    date = date_match.group(1) if date_match else None

    guests_match = re.search(guests_pattern, file_content)
    guests = [guest.strip().strip('"') for guest in guests_match.group(1).split(",")] if guests_match else []

    series_match = re.search(series_pattern, file_content)
    series = [s.strip().strip('"').lower() for s in series_match.group(1).split(",")] if series_match else []

    episode_match = re.search(episode_pattern, file_content)
    episode = int(episode_match.group(1)) if episode_match else float('inf')  # Treat missing episodes as last

    return date, guests, series, episode

def process_files(directory, series_filter, within_days, exclude_guests, verbose):
    """Process all files in the directory to extract guest appearance data."""
    guest_appearance = {}
    cutoff_date = datetime.now() - timedelta(days=within_days)
    files_with_episodes = []

    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return {}

    # Read all files and extract episode numbers
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r") as file:
                content = file.read()
                date_str, guests, series, episode = extract_fields(content)
                files_with_episodes.append((filename, date_str, guests, series, episode, content))

    # Sort files based on episode number
    files_with_episodes.sort(key=lambda x: x[4])  # Sort by episode

    for filename, date_str, guests, series, episode, content in files_with_episodes:
        if series_filter != "" and series_filter not in series:
            if verbose:
                print(f"Filtering out {filename} - series: {series}")
            continue

        if verbose:
            print(f"Continuing to process {filename} - Date: {date_str}, Episode: {episode}")

        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
            except ValueError:
                if verbose:
                    print(f"Skipping {filename}: Invalid date format {date_str}")
                continue

            if date < cutoff_date:
                days_ago = (datetime.now() - date).days
                if verbose:
                    print(f"Skipping {filename}: Episode aired {days_ago} days ago ({date})")
                continue

            for guest in guests:
                if guest in exclude_guests:
                    if verbose:
                        print(f"Excluding guest {guest} from processing.")
                    continue

                if guest in guest_appearance:
                    # Update only if this appearance is more recent
                    if date > guest_appearance[guest][0]:
                        guest_appearance[guest] = (date, episode)
                else:
                    guest_appearance[guest] = (date, episode)

    return guest_appearance

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process podcast episodes.")
    parser.add_argument(
        "--directory", type=str, default="./content/episode/",
        help="Directory containing the podcast episode files (default: './content/episode/')."
    )
    parser.add_argument(
        "--series_filter", type=str, default="wir",
        help="Series to filter (default: 'wir')."
    )
    parser.add_argument(
        "--within_days", type=int, default=1000,
        help="Consider episodes aired within the last number of days (default: 365)."
    )
    parser.add_argument(
        "--exclude_guests", type=str, default="",
        help="Comma-separated list of guests to exclude (default: none)."
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose output."
    )
    parser.add_argument(
        "--output_json", type=str, help="Path to save output as JSON (optional)."
    )
    args = parser.parse_args()

    # Convert exclude_guests string into a list
    exclude_guests = [guest.strip() for guest in args.exclude_guests.split(",") if guest.strip()]

    # Process files with command-line arguments
    guest_appearance = process_files(
        args.directory,
        args.series_filter.lower(),
        args.within_days,
        exclude_guests,
        args.verbose
    )

    # Sort by last appearance date
    sorted_guests = sorted(guest_appearance.items(), key=lambda x: x[1][0])  # Sort by date

    # Output results
    print(f"Processed {len(sorted_guests)} guests from episodes within the last {args.within_days} days.")
    if not sorted_guests:
        print("No episodes found matching the criteria.")
        return

    print("\n=== Guest Appearances ===")
    for guest, (date, episode) in sorted_guests:
        print(f"{guest}: Episode {episode}, Date {date.date()}")

    if args.output_json:
        # Save output with episode numbers
        json_output = {guest: {"date": date.isoformat(), "episode": episode} for guest, (date, episode) in sorted_guests}
        with open(args.output_json, "w") as json_file:
            json.dump(json_output, json_file, indent=4)
        print(f"Results saved to {args.output_json}")

if __name__ == "__main__":
    main()

