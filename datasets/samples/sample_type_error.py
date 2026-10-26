"""Sample Python code with intentional type errors for semantic analysis and ML evaluation."""

def calculate_discount(price: float, discount_percent: float) -> float:
    # Error: Returning a string instead of float
    if discount_percent < 0 or discount_percent > 100:
        return "Invalid discount"  # Incompatible return type
    return price * (1.0 - (discount_percent / 100.0))


def format_user_badge(username: str, level: int) -> str:
    # Error: Concatenating str and int directly without str() conversion
    badge = username + "_" + level  # Type mismatch in binary operation
    return badge.upper()


def get_account_balance(user_id: str) -> float:
    account: dict[str, float] | None = None
    if user_id == "admin":
        account = {"balance": 1000.50}

    # Error: Potential None dereference without guard
    return account["balance"]  # None-safety issue
