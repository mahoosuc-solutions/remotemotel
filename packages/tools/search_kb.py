def search_kb(query: str, top_k: int = 5):
    policies = [
        {"title": "Pet Policy", "content": "Pets are welcome for $20 per night."},
        {"title": "Check-in", "content": "Check-in time is after 4 PM."},
        {"title": "Checkout", "content": "Checkout time is by 10 AM."},
    ]
    return [p for p in policies if query.lower() in p["title"].lower()]
