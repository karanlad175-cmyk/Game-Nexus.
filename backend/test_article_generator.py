from app.ai_automation.article_generator import generate_article

test_article = {
    "category": "PlayStation",
    "title": "PlayStation 5 update introduces custom game collections",
"summary": (
    "Sony has announced a software update for PlayStation 5. "
    "The update introduces a redesigned system interface. "
    "PlayStation 5 users will be able to organize their "
    "installed games into custom collections. The update "
    "also includes improvements to system performance and "
    "stability. Sony says the update will begin rolling out "
    "to PlayStation 5 users this month. Further regional "
    "availability details have not yet been provided."
),
    "source": "Example Gaming News",
    "link": "https://example.com/playstation-accessibility-news"
}

print("Generating test article...")

article = generate_article(test_article)

print("\n========== GENERATED ARTICLE ==========")
print("Publish decision:", article["should_publish"])
print("Title:", article["title"])
print("Category:", article["category"])
print("Publisher:", article["source"])
print("Source URL:", article["source_url"])

print("\n========== ARTICLE BODY ==========")
print(article["body"])

print("\n========== ATTRIBUTION CHECK ==========")
print(
    "Publisher found:",
    "Example Gaming News" in article["body"]
)

print(
    "Source link found:",
    "https://example.com/playstation-accessibility-news"
    in article["body"]
)