import type { CodeSample } from '../types/editor'

export const CODE_SAMPLES: CodeSample[] = [
  // --- Python Samples ---
  {
    id: 'sample-clean',
    name: 'Valid Program',
    language: 'python',
    description: 'Fully typed Python function with no type errors or anomalies.',
    code: `def calculate_order_total(items: list, tax_rate: float, discount: float = 0.0) -> float:
    """Compute final order price after applying discount and sales tax."""
    subtotal: float = sum(items)
    discounted_total: float = subtotal * (1.0 - discount)
    final_amount: float = discounted_total * (1.0 + tax_rate)
    return round(final_amount, 2)


cart_prices: list = [19.99, 45.50, 12.00]
total: float = calculate_order_total(cart_prices, 0.08, 0.10)
print(f"Total: \${total}")
`,
  },
  {
    id: 'sample-type-mismatch',
    name: 'String + Number Concat (TM001)',
    language: 'python',
    description: 'Direct string concatenation with an integer without explicit str() casting.',
    code: `def create_user_badge(username: str, user_id: int) -> str:
    """Generate display badge string for registered user."""
    # Attempting to concatenate str with int directly
    badge: str = "User#" + user_id
    return badge


result: str = create_user_badge("alice", 1042)
print(result)
`,
    expectedCategory: 'type_mismatch',
  },
  {
    id: 'sample-incompatible-return',
    name: 'Incompatible Return (TM005)',
    language: 'python',
    description: 'Function declared to return int returns a string literal.',
    code: `def parse_user_age(raw_input: str) -> int:
    """Parse integer age, returning string default when missing."""
    if not raw_input:
        # Declared return type is int, but returning a str
        return "N/A"
    return int(raw_input)


user_age: int = parse_user_age("")
`,
    expectedCategory: 'incompatible_return',
  },
  {
    id: 'sample-arg-count',
    name: 'Argument Count Mismatch (TM003)',
    language: 'python',
    description: 'Function called with missing required parameters.',
    code: `def transfer_funds(sender: str, recipient: str, amount: float) -> bool:
    """Transfer funds between two verified user accounts."""
    if amount <= 0:
        return False
    print(f"Transferred \${amount} from {sender} to {recipient}")
    return True


# Error: transfer_funds requires 3 positional arguments, but only 2 provided
success: bool = transfer_funds("user_alice", "user_bob")
`,
    expectedCategory: 'argument_count_mismatch',
  },

  // --- TypeScript Samples ---
  {
    id: 'sample-ts-type-mismatch',
    name: 'Type Mismatch (TS2322)',
    language: 'typescript',
    description: 'Assigning a string expression to a variable explicitly typed as number.',
    code: `interface OrderSummary {
  id: string
  totalAmount: number
  isPaid: boolean
}

function processPayment(order: OrderSummary): number {
  // Error: Type 'string' is not assignable to type 'number'
  let fee: number = "15.00"
  return order.totalAmount + fee
}

const myOrder: OrderSummary = { id: "ORD-9021", totalAmount: 120.50, isPaid: false }
console.log(processPayment(myOrder))
`,
    expectedCategory: 'type_mismatch',
  },
  {
    id: 'sample-ts-valid',
    name: 'Valid TypeScript Program',
    language: 'typescript',
    description: 'Valid, strongly-typed TypeScript program with clean interfaces and generics.',
    code: `interface UserProfile {
  id: number
  username: string
  roles: string[]
}

function hasAdminRole(user: UserProfile): boolean {
  return user.roles.includes("admin")
}

const currentUser: UserProfile = {
  id: 42,
  username: "alex_dev",
  roles: ["developer", "admin"],
}

console.log("Is Admin:", hasAdminRole(currentUser))
`,
  },

  // --- JavaScript Samples ---
  {
    id: 'sample-js-type-mismatch',
    name: 'JSDoc Type Mismatch',
    language: 'javascript',
    description: 'JavaScript with JSDoc type annotations detected by static analyzer.',
    code: `/**
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
function addNumbers(a, b) {
  return a + b
}

/** @type {number} */
let result = addNumbers("10", 20)
console.log(result)
`,
    expectedCategory: 'type_mismatch',
  },
  {
    id: 'sample-js-valid',
    name: 'Valid JavaScript Program',
    language: 'javascript',
    description: 'Clean JavaScript program without syntax or type errors.',
    code: `function computeMetrics(values) {
  const sum = values.reduce((acc, curr) => acc + curr, 0)
  const average = values.length > 0 ? sum / values.length : 0
  return { sum, average }
}

const stats = computeMetrics([10, 20, 30, 40])
console.log("Metrics:", stats)
`,
  },

  // --- Java Samples ---
  {
    id: 'sample-java-type-mismatch',
    name: 'Incompatible Types (Java)',
    language: 'java',
    description: 'Java compiler type error: String cannot be converted to int.',
    code: `public class Main {
    public static int calculateScore(int baseScore, double multiplier) {
        // Error: incompatible types: String cannot be converted to int
        int bonus = "50";
        return (int)(baseScore * multiplier) + bonus;
    }

    public static void main(String[] args) {
        int finalScore = calculateScore(100, 1.5);
        System.out.println("Final score: " + finalScore);
    }
}
`,
    expectedCategory: 'type_mismatch',
  },
  {
    id: 'sample-java-valid',
    name: 'Valid Java Program',
    language: 'java',
    description: 'Clean Java program with proper static typing.',
    code: `public class Main {
    public static double computeTotal(double price, double taxRate) {
        return price * (1.0 + taxRate);
    }

    public static void main(String[] args) {
        double total = computeTotal(49.99, 0.08);
        System.out.println("Total: " + total);
    }
}
`,
  },

  // --- C Samples ---
  {
    id: 'sample-c-type-mismatch',
    name: 'Incompatible Assignment (C)',
    language: 'c',
    description: 'C compiler diagnostic: assigning pointer to incompatible integer.',
    code: `#include <stdio.h>

int main() {
    // Error: assigning 'char *' to incompatible type 'int'
    int count = "100";
    printf("Count: %d\\n", count);
    return 0;
}
`,
    expectedCategory: 'type_mismatch',
  },

  // --- C++ Samples ---
  {
    id: 'sample-cpp-type-mismatch',
    name: 'Cannot Convert Type (C++)',
    language: 'cpp',
    description: 'C++ static type check error: cannot convert const char* to int.',
    code: `#include <iostream>
#include <string>

int computeFactor(int factor) {
    // Error: cannot convert 'const char*' to 'int' in assignment
    int multiplier = "5";
    return factor * multiplier;
}

int main() {
    std::cout << computeFactor(10) << std::endl;
    return 0;
}
`,
    expectedCategory: 'type_mismatch',
  },

  // --- Go Samples ---
  {
    id: 'sample-go-type-mismatch',
    name: 'Mismatched Types (Go)',
    language: 'go',
    description: 'Go type error: cannot use string as type int.',
    code: `package main

import "fmt"

func calculateArea(width int, height int) int {
    // Error: cannot use "20" (untyped string constant) as int value in assignment
    var margin int = "20"
    return (width * height) + margin
}

func main() {
    fmt.Println(calculateArea(10, 5))
}
`,
    expectedCategory: 'type_mismatch',
  },

  // --- Rust Samples ---
  {
    id: 'sample-rust-type-mismatch',
    name: 'Mismatched Types (Rust E0308)',
    language: 'rust',
    description: 'Rust compiler diagnostic E0308: expected i32, found &str.',
    code: `fn compute_latency(base_ms: i32) -> i32 {
    // Error [E0308]: mismatched types: expected \`i32\`, found \`&str\`
    let jitter: i32 = "5ms";
    base_ms + jitter
}

fn main() {
    println!("Latency: {}", compute_latency(45));
}
`,
    expectedCategory: 'type_mismatch',
  },
]

/**
 * Filter available samples matching the currently selected programming language.
 * Falls back to default Python samples if none match.
 */
export function getSamplesForLanguage(languageId: string): CodeSample[] {
  const norm = (languageId || 'python').toLowerCase()
  const matching = CODE_SAMPLES.filter(s => (s.language || 'python').toLowerCase() === norm)
  return matching.length > 0 ? matching : CODE_SAMPLES.filter(s => (s.language || 'python') === 'python')
}
