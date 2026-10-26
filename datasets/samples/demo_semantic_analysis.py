"""Documented sample program demonstrating TypeMind AI semantic analyzer checks."""

def compute_total(base_price: float, tax_rate: float) -> float:
    # Check 1: Incompatible return type (returns str instead of float)
    if tax_rate < 0.0:
        return "Invalid tax rate"
    return base_price * (1.0 + tax_rate)


def format_order_id(prefix: str, order_num: int) -> str:
    # Check 2: String-number concatenation mismatch
    order_id = prefix + "-" + order_num
    return order_id


def process_orders() -> None:
    # Check 3: Unsupported arithmetic on sequences
    bad_math = "receipt" - "summary"

    # Check 4: Function argument count mismatch (expects 2 args, provided 1)
    compute_total(100.0)

    # Check 5: Annotated argument type mismatch (expects int, received str)
    format_order_id("ORD", "not-a-number")

    # Check 6: Annotated assignment mismatch
    active_count: int = "twenty"

    # Check 7: Reassignment inconsistency (variable inferred as int, reassigned to list)
    retries = 3
    retries = [1, 2, 3]


if __name__ == "__main__":
    process_orders()
