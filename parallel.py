import requests
from bs4 import BeautifulSoup
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# =========================================================
# 1. FIND 50 BBC ARTICLE URLs AUTOMATICALLY
# =========================================================

def get_article_urls():

    url = "https://www.bbc.com/news"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    print("BBC status code:", response.status_code)

    soup = BeautifulSoup(response.text, "html.parser")

    article_urls = set()

    for link in soup.find_all("a", href=True):

        href = link["href"]

        # BBC article links
        if href.startswith("/news/articles/"):

            full_url = "https://www.bbc.com" + href

            article_urls.add(full_url)

    article_urls = list(article_urls)

    return article_urls[:50]


# =========================================================
# 2. SCRAPE ONE ARTICLE
# =========================================================

def scrape_article(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        soup = BeautifulSoup(response.text, "html.parser")


        # -------------------------
        # TITLE
        # -------------------------

        title_tag = soup.find("h1")

        title = ""

        if title_tag:
            title = title_tag.get_text(" ", strip=True)


        # -------------------------
        # DESCRIPTION
        # -------------------------

        description = ""

        meta = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if meta:
            description = meta.get("content", "").strip()


        # -------------------------
        # ARTICLE CONTENT
        # -------------------------

        paragraphs = soup.select("main p")

        content_list = []

        for paragraph in paragraphs:

            text = paragraph.get_text(" ", strip=True)

            if text:
                content_list.append(text)

        content = "\n".join(content_list)


        # -------------------------
        # PUBLISHED DATE
        # -------------------------

        published_date = ""

        time_tag = soup.find("time")

        if time_tag:

            published_date = (
                time_tag.get("datetime")
                or time_tag.get_text(" ", strip=True)
            )


        return {
            "url": url,
            "title": title,
            "description": description,
            "content": content,
            "published_date": published_date
        }


    except Exception as e:

        print("ERROR:", url)
        print(e)

        return {
            "url": url,
            "title": "",
            "description": "",
            "content": "",
            "published_date": ""
        }


# =========================================================
# 3. GET URLS AUTOMATICALLY
# =========================================================

urls = get_article_urls()

print("\n================================")
print("ARTICLE URLS FOUND:", len(urls))
print("================================")

for i, url in enumerate(urls, 1):

    print(i, url)


# =========================================================
# 4. PARALLEL SCRAPING
# =========================================================

print("\nStarting parallel scraping...\n")

start_time = time.time()

results = []


with ThreadPoolExecutor(max_workers=20) as executor:

    futures = []

    for url in urls:

        future = executor.submit(
            scrape_article,
            url
        )

        futures.append(future)


    for future in as_completed(futures):

        result = future.result()

        results.append(result)

        print(
            f"Completed {len(results)}/{len(urls)} | "
            f"{result['title'][:70]}"
        )


# =========================================================
# 5. SAVE RESULTS
# =========================================================

with open(
    "bbc_articles_parallel.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "url",
            "title",
            "description",
            "content",
            "published_date"
        ]
    )

    writer.writeheader()

    writer.writerows(results)


# =========================================================
# 6. FINISHED
# =========================================================

end_time = time.time()

print("\n========================================")
print("PARALLEL SCRAPING COMPLETED")
print("========================================")

print("Articles:", len(results))
print("Threads:", 20)
print("Time:", round(end_time - start_time, 2), "seconds")
print("File: bbc_articles_parallel.csv")