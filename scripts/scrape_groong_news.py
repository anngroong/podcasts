#!/usr/bin/env python3

import re
import json
import requests
from bs4 import BeautifulSoup
from weasyprint import HTML

# Configuration
BASE_URL = "https://groong.org/news/index.html"
DOMAIN = "https://groong.org"
MAX_ARTICLES = 1000

def get_article_links(index_url):
    response = requests.get(index_url)
    if response.status_code != 200:
        print("Failed to retrieve the index page")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    pattern = re.compile(r"msg[0-9]+\.html")

    for a_tag in soup.find_all("a", href=True):
        url = a_tag["href"]
        if pattern.match(url):
            full_url = f"{DOMAIN}/news/{url}"
            links.append(full_url)

    return links

def scrape_article(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve article: {url}")
        return {"title": "Untitled Article", "groong_link": url, "content": ""}

    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled Article"

    content_div = soup.find("div", attrs={"dir": "ltr"})
    if content_div:
        content = content_div.get_text(separator="\n", strip=True)
    else:
        print(f"No content found for: {url}")
        content = "(Content could not be extracted)"

    return {
        "title": title,
        "groong_link": url,
        "content": content
    }

def save_as_text(articles, filename="all_news.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        for article in articles:
            file.write(f"\n\n=====\n\nGROONG LINK: {article['groong_link']}\n\nTitle: {article['title']}\n\n{article['content']}\n")
    print(f"Text version saved as {filename}")

def save_as_pdf(articles, filename="all_news.pdf"):
    css_styles = """
        @page { size: A4; margin: 1in; }
        body {
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            text-align: justify;
            white-space: pre-wrap;
        }
        h1 { font-size: 16pt; font-weight: bold; }
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
    html_content = f"<html><head><style>{css_styles}</style></head><body><h1>Collected News Articles</h1>"

    for article in articles:
        html_content += f"""
        <div class="article">
            <div class="title">{article['title']}</div>
            <div><b>GROONG LINK:</b> <a href="{article['groong_link']}">{article['groong_link']}</a></div>
            <div>{article['content'].replace('\n', '<br>')}</div>
        </div>
        """

    html_content += "</body></html>"

    HTML(string=html_content).write_pdf(filename)
    print(f"PDF saved as {filename}")

def save_as_json(articles, filename="all_news.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(articles, file, indent=2, ensure_ascii=False)
    print(f"JSON saved as {filename}")

def scrape_all_news():
    article_urls = get_article_links(BASE_URL)
    scraped_articles = []

    for index, url in enumerate(article_urls):
        if index >= MAX_ARTICLES:
            break
        print(f"Scraping ({index+1}/{MAX_ARTICLES}): {url}")
        article_data = scrape_article(url)
        scraped_articles.append(article_data)

    if scraped_articles:
        save_as_text(scraped_articles)
        save_as_pdf(scraped_articles)
        save_as_json(scraped_articles)
    else:
        print("No news articles were found.")

if __name__ == "__main__":
    scrape_all_news()

