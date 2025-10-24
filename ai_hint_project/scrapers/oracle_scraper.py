import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


print("📍 Current working directory:", os.getcwd())

BASE_URL = "https://docs.oracle.com/javase/tutorial/"
OUTPUT_DIR = "oracle_articles"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_trail_links():
    resp = requests.get(BASE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("java/") and href.endswith("index.html"):
            full_url = urljoin(BASE_URL, href)
            links.append(full_url)
    return links

def get_lesson_links(trail_url):
    resp = requests.get(trail_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    base = trail_url.rsplit("/", 1)[0] + "/"
    lessons = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".html") and not href.startswith("http"):
            lessons.append(urljoin(base, href))
    return lessons

def scrape_lesson(url):
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Untitled"
        text = soup.get_text(separator="\n", strip=True)
        filename = os.path.join(OUTPUT_DIR, title.replace(" ", "_")[:50] + ".txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Saved: {title}")
    except Exception as e:
        print(f"❌ Failed: {url} — {e}")

def main():
    trails = get_trail_links()
    print(f"🔗 Found {len(trails)} trails")
    for trail in trails:
        lessons = get_lesson_links(trail)
        print(f"📚 Trail: {trail} — {len(lessons)} lessons")
        for lesson in lessons:
            scrape_lesson(lesson)

if __name__ == "__main__":
    main()
