# TypeMind AI - Datasets Specification

## 1. Overview
The TypeMind AI dataset repository provides curated Python code snippets for evaluating static semantic type rules and training baseline machine learning classification models.

> [!IMPORTANT]
> **Synthetic Data Notice**:
> All examples in `datasets/type_patterns_dataset.json` are **synthetically authored** for unit verification, baseline benchmarking, and reproducible pipeline construction. This initial synthetic dataset does **not** claim to represent real-world distribution, developer typing habits, or large-scale production codebases.

---

## 2. Dataset Schema

Each record in `type_patterns_dataset.json` conforms to the following schema:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Unique identifier (e.g., `SYN-CONCAT-001`) |
| `code` | `string` | Raw Python code snippet |
| `target_label` | `string` | Ground-truth classification label |
| `category` | `string` | High-level pattern category (`valid`, `binary_op`, `call`, `return`, `assignment`) |
| `group_id` | `string` | Conceptual pattern group used for group-aware and leak-free train/test splitting |
| `origin` | `string` | Origin flag (`synthetic`) |
| `description` | `string` | Human-readable explanation of the pattern |

---

## 3. Ground Truth Labels

The target labels correspond to the semantic type categories identified by the TypeMind analyzer:

1. **`no_error`**: Valid Python programs exhibiting correct typing, valid operations, and matching signatures.
2. **`type_mismatch`**: Concatenation or operations on incompatible types (e.g. `str + int`).
3. **`unsupported_operand`**: Arithmetic operations unsupported by the operand types (e.g. `str - str`, `None + int`).
4. **`argument_count_mismatch`**: Calling a function with missing required arguments or excessive positional arguments.
5. **`argument_type_mismatch`**: Providing arguments whose types violate function parameter annotations.
6. **`incompatible_return`**: Function return statements that produce values incompatible with declared return annotations.
7. **`invalid_assignment`**: Assigning values incompatible with explicit variable type annotations.

---

## 4. Leakage Prevention & Data Limitations

- **Group-Aware Splitting**: Samples with similar semantic structures share a `group_id`. Train and test splits are partitioned by group to prevent model memorization of identical expression patterns.
- **Abstract Feature Extraction**: The feature extractor discards specific variable names, line numbers, and file identifiers, focusing exclusively on AST operator structures, inferred type properties, and signature counts.
- **Known Limitations**:
  - Small sample size (42 initial curated samples) intended for baseline classification and reproducible pipeline verification.
  - Does not cover complex multi-inheritance class hierarchies, metaprogramming, or asynchronous generators.
