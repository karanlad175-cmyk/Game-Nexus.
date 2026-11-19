from app.ai_automation.rss_reader import fetch_rss_articles

print("Fetching gaming news...")

articles = fetch_rss_articles()

print("\nTotal articles:", len(articles))

for article in articles[:10]:
    print("\nTitle:", article["title"])
    print("Category:", article["category"])
    print("Source:", article["source"])
    print("Content length:", len(article["summary"]))
    print("Content preview:", article["summary"][:300])