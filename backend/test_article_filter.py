from app.ai_automation.rss_reader import fetch_rss_articles
from app.ai_automation.article_filter import filter_gaming_articles

print("Fetching RSS articles...")

articles = fetch_rss_articles()

print("\nTotal RSS articles:", len(articles))

filtered = filter_gaming_articles(articles)

print("Gaming-relevant articles:", len(filtered))
print("Rejected articles:", len(articles) - len(filtered))

print("\n========== FILTERED ARTICLES ==========")

for article in filtered:
    print(
        f'{article["category"]} | {article["title"]}'
    )