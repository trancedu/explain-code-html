# Explain Code in HTML

An agent skill that turns a source file into a standalone HTML reading companion, combining the big picture with detailed, source-grounded implementation explanations.

## What it produces

- A file overview and navigable execution flow.
- Complete source divided into annotated logical blocks, with original line numbers.
- Concrete examples, intermediate values, edge cases and implementation limitations.
- Self-check questions and copyable follow-up prompts.
- A high-contrast single-column layout with no network dependencies.
- Source provenance and a SHA-256 hash to help identify stale explanations.

The goal is to help developers understand and verify code rather than rely on an AI summary alone. This skill does not automatically synchronize explanations or guarantee that generated explanations are correct.

## Usage

Add this repository's skill directory to the skills location supported by your coding agent, then ask:

> Use $explain-code-html to turn path/to/source.py into a detailed HTML reading companion.

The skill instructions are written in English. Generated explanations follow the language requested by the user.

See [SKILL.md](SKILL.md) for the complete workflow and explanation requirements.

## Example

The [examples](examples/) directory contains a complete, runnable demonstration:

- [expense_pipeline.py](examples/expense_pipeline.py): a 99-line Python program that normalizes, categorizes, deduplicates and summarizes sample expenses.
- [expense_pipeline.html](examples/expense_pipeline.html): its standalone reading companion, including an overview, execution flow, detailed source explanations, executed examples and self-check questions.

Download the HTML file and open it in a browser; it works offline. GitHub's file view displays the HTML source rather than the rendered guide.

Run the sample with Python 3.9 or newer:

```sh
python3 examples/expense_pipeline.py
```

The sample accepts four expenses, detects one duplicate, rejects one invalid amount and reports a total of 5,101 cents. The guide also explains the limitations of the sample's deduplication and amount-validation rules.
