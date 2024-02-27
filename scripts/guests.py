#!.venv/bin/python

# A script to help determine which guests to schedule.

import glob
import frontmatter
import markdown

dir_path = './content/episode/*.md'
within_days = 100

for file in glob.glob(dir_path, recursive=True):
    print(file)
    post = frontmatter.load(file)
    print(post.keys())
    break
