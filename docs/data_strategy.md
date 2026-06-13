# SalesMirror Data Strategy

This project is for learning and testing sales call analysis before doing any model training.

## What a Transcript Is

A transcript is the written version of a call. For SalesMirror, a transcript should show who said what:

```text
Salesperson: Thanks for joining today.
Customer: Happy to talk.
```

The transcript is the input that the analysis system reads.

## What a Label or Ideal Analysis Is

A label is the ideal answer we want the model to produce for a transcript.

For SalesMirror, the label is a JSON coaching report with scores, mistakes, missed questions, suggested improvements, better responses, and a short summary. Good labels are important because they define what "good analysis" means.

## Why We Are Not Fine-Tuning Yet

We are not fine-tuning yet because the project first needs a clear rubric, good prompts, and enough examples to evaluate output quality.

Fine-tuning too early can lock in weak labels, bad scoring habits, or unrealistic examples. It is better to first test whether a local model with a strong prompt can produce useful reports.

## How to Create Safe Synthetic Sales Calls

Synthetic calls are made-up examples. They are safest for early testing because they do not contain real customer information.

Good synthetic calls should:

- Use realistic sales conversations.
- Include clear sales behaviors such as opening, discovery, objections, and closing.
- Avoid real company names, phone numbers, email addresses, prices, contracts, and private details.
- Cover different call quality levels: strong, weak, mixed, price objection, no decision, poor follow-up.

## How to Anonymize Real Calls

Do not use real customer calls unless consent and privacy controls are handled.

If a real call is approved for internal testing, remove or replace:

- Names of people.
- Company names.
- Email addresses and phone numbers.
- Contract details.
- Exact pricing.
- Customer identifiers.
- Private business plans or sensitive objections.

Use placeholders such as `[Customer Name]`, `[Company]`, `[Email]`, and `[Price]`.

## How Many Examples Before Fine-Tuning

For learning and prompt testing, a small set of 10 to 30 synthetic examples is enough.

Before fine-tuning, aim for at least 100 to 300 high-quality labeled examples. More may be needed if the calls vary by industry, sales motion, language, or call type.

The quality of labels matters more than raw quantity. Ten excellent examples are more useful than fifty inconsistent examples.

## Why Evaluate Prompt Quality Before Model Training

Prompt evaluation tells us whether the rubric, JSON format, and instructions are clear enough.

Before training, we should test:

- Does the model return valid JSON?
- Are the scores consistent?
- Does the feedback match the transcript?
- Does it catch missed discovery and weak closing?
- Does it handle price objections well?
- Does the report help a salesperson improve?

If prompt quality is poor, fine-tuning will not fix the real problem. The rubric and labels should be improved first.
