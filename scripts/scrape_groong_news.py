#!/usr/bin/env python3

import re
import requests
from bs4 import BeautifulSoup
from weasyprint import HTML

# Base URL
BASE_URL = "https://groong.org/news/index.html"
DOMAIN = "https://groong.org"
MAX_ARTICLES = 1000  # Set your desired maximum number of articles


def get_article_links(index_url):
    response = requests.get(index_url)
    if response.status_code != 200:
        print("Failed to retrieve the index page")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    # Regular expression to match URLs like msg161794.html
    pattern = re.compile(r"msg[0-9]+\.html")

    for a_tag in soup.find_all("a", href=True):
        url = a_tag["href"]

        # Check if URL matches the pattern
        if pattern.match(url):
            full_url = f"{DOMAIN}/news/{url}"  # Ensure correct full URL format
            links.append(full_url)

    return links

# Function to scrape content from an article page
def scrape_article(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve article: {url}")
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled Article"

    # Extract content inside <div dir="ltr">
    article_content = soup.find("div", attrs={"dir": "ltr"})

    if article_content:
        text_content = article_content.get_text(separator="\n", strip=True)
        return f"Title: {title}\n\n{text_content}"  # Prepend the title to the content
    else:
        print(f"No content found for: {url}")
        return f"Title: {title}\n\n(Content could not be extracted)"

# Function to save content as a text file
def save_as_text(content, filename="all_news.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"News saved as {filename}")

# Function to save content as a PDF using WeasyPrint
def save_as_pdf(text, filename="all_news.pdf"):
    css_styles = """
        @page {
            size: A4;
            margin: 1in;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            text-align: justify;
            white-space: pre-wrap;
        }
        h1 {
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .article {
            margin-bottom: 30px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
        }
        .title {
            font-size: 14pt;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
    """

    html_content = f"""
    <html>
    <head>
        <style>{css_styles}</style>
    </head>
    <body>
        <h1>Collected News Articles</h1>
        <div class="article">
            {text.replace("\n", "<br>")}
        </div>
    </body>
    </html>
    """

    HTML(string=html_content).write_pdf(filename)
    print(f"PDF saved as {filename}")

# Main function to scrape all news and save
def scrape_all_news():
    article_urls = get_article_links(BASE_URL)
    all_news = ""

    # Limit the number of articles processed
    for index, url in enumerate(article_urls):
        if index >= MAX_ARTICLES:
            break  # Stop scraping if we've reached the limit

        print(f"Scraping ({index+1}/{MAX_ARTICLES}): {url}")
        article_text = scrape_article(url)
        all_news += f"\n\n=== ARTICLE FROM {url} ===\n\n{article_text}"

    if all_news.strip():
        save_as_text(all_news)
        save_as_pdf(all_news)
    else:
        print("No news articles were found.")


if __name__ == "__main__":
    scrape_all_news()

