# TypeMind AI - Machine Learning Pipeline Evaluation Report

**Model Name:** `TypeMind_PatternClassifier` (v1.0.0)  
**Evaluation Timestamp:** `2026-10-26T14:47:58.514432+00:00`  
**Chosen Architecture:** `RandomForestClassifier`  

> [!IMPORTANT]
> **Dataset Origin & Limitations:**
> The evaluation was conducted on `42` synthetically authored Python code patterns.
> This synthetic benchmark confirms reproducible pipeline mechanics, abstract feature vectorization, and model persistence.
> It does **not** represent real-world software project distribution.

---

## 1. Baseline Model Comparison

| Architecture | Precision (Macro) | Recall (Macro) | F1-Score (Macro) | F1-Score (Weighted) |
| :--- | :--- | :--- | :--- | :--- |
| **LogisticRegression** | 0.6667 | 0.6905 | 0.6143 | 0.6152 |
| **RandomForestClassifier** | 0.6190 | 0.6905 | 0.6190 | 0.6061 |

---

## 2. Per-Class Test Performance

| Class / Target Label | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| `argument_count_mismatch` | 0.5000 | 1.0000 | 0.6667 | 1 |
| `argument_type_mismatch` | 0.0000 | 0.0000 | 0.0000 | 1 |
| `incompatible_return` | 1.0000 | 1.0000 | 1.0000 | 1 |
| `invalid_assignment` | 0.5000 | 1.0000 | 0.6667 | 1 |
| `no_error` | 0.3333 | 0.3333 | 0.3333 | 3 |
| `type_mismatch` | 1.0000 | 1.0000 | 1.0000 | 2 |
| `unsupported_operand` | 1.0000 | 0.5000 | 0.6667 | 2 |

---

## 3. Confusion Matrix

Row = Ground Truth, Column = Predicted

| Ground Truth \ Predicted | `argument_count_mismatch` | `argument_type_mismatch` | `incompatible_return` | `invalid_assignment` | `no_error` | `type_mismatch` | `unsupported_operand` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`argument_count_mismatch`** | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **`argument_type_mismatch`** | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| **`incompatible_return`** | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| **`invalid_assignment`** | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| **`no_error`** | 1 | 0 | 0 | 1 | 1 | 0 | 0 |
| **`type_mismatch`** | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| **`unsupported_operand`** | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

---

## 4. Dataset Class Distribution

| Class | Sample Count | Percentage |
| :--- | :--- | :--- |
| `argument_count_mismatch` | 5 | 11.9% |
| `argument_type_mismatch` | 5 | 11.9% |
| `incompatible_return` | 5 | 11.9% |
| `invalid_assignment` | 5 | 11.9% |
| `no_error` | 10 | 23.8% |
| `type_mismatch` | 6 | 14.3% |
| `unsupported_operand` | 6 | 14.3% |