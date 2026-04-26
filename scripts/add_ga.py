#!/usr/bin/env python3

# Traverse directory with HTML files and add GA analytics header to all static
# files.

import os
import argparse

MARKER = b"G-Q6HJ52LZ77"

SNIPPET = b"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q6HJ52LZ77"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-Q6HJ52LZ77');
</script>
"""


def excluded(path, root_dir, exclude_dirs):
    rel = os.path.relpath(path, root_dir)
    for ex in exclude_dirs:
        if rel == ex or rel.startswith(ex + os.sep):
            return True
    return False


def process_file(path, test_mode=False):
    with open(path, "rb") as f:
        content = f.read()

    if MARKER in content:
        return "SKIP"

    idx = content.lower().find(b"</head>")

    if idx == -1:
        return "NOHEAD"

    if test_mode:
        print(f"WOULD UPDATE: {path}")
        return "WOULD"

    new_content = (
        content[:idx] +
        b"\n" + SNIPPET + b"\n" +
        content[idx:]
    )

    backup = path + ".bak"

    if not os.path.exists(backup):
        os.rename(path, backup)
    else:
        os.remove(path)

    with open(path, "wb") as f:
        f.write(new_content)

    print(f"UPDATED: {path}")
    return "UPDATED"


def main():
    parser = argparse.ArgumentParser(
        description="Inject Google Analytics snippet into HTML files."
    )

    parser.add_argument(
        "root",
        help="Root directory to scan"
    )

    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Dry run - show files that would change"
    )

    parser.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=["news"],
        help="Subdirectory to exclude (repeatable)"
    )

    args = parser.parse_args()

    stats = {
        "updated": 0,
        "would": 0,
        "skipped": 0,
        "nohead": 0
    }

    for root, dirs, files in os.walk(args.root):

        if excluded(root, args.root, args.exclude):
            dirs[:] = []
            continue

        dirs[:] = [
            d for d in dirs
            if not excluded(os.path.join(root, d), args.root, args.exclude)
        ]

        for file in files:
            if not file.lower().endswith(".html"):
                continue

            result = process_file(
                os.path.join(root, file),
                test_mode=args.test
            )

            if result == "UPDATED":
                stats["updated"] += 1
            elif result == "WOULD":
                stats["would"] += 1
            elif result == "SKIP":
                stats["skipped"] += 1
            elif result == "NOHEAD":
                stats["nohead"] += 1

    print("\nSummary")
    print("-------")
    if args.test:
        print(f"Would update: {stats['would']}")
    else:
        print(f"Updated:      {stats['updated']}")

    print(f"Skipped:      {stats['skipped']}")
    print(f"No </head>:   {stats['nohead']}")


if __name__ == "__main__":
    main()
