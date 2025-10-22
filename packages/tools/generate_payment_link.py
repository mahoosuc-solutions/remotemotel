def generate_payment_link(amount_cents: int, description: str):
    return {"url": f"https://example.com/pay/{description.replace(' ', '-')}-{amount_cents}"}
