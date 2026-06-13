# SalesMirror Model Review Template

Use this template after running `backend/scripts/compare_ollama_models.py`.

## Review Metadata

- Date:
- Reviewer:
- Models compared:
- Sample transcripts used:

## JSON Reliability

- Did the model return valid JSON every time?
- Did every output match the SalesMirror schema?
- Did arrays contain enough useful items?
- Any repeated formatting failures?

Notes:

## Sales Reasoning Quality

- Did the model correctly identify strong and weak calls?
- Were scores too generous, too harsh, or reasonable?
- Did the feedback match evidence in the transcript?

Notes:

## Objection Detection

- Did the model detect objections?
- Did it distinguish price objections from general objections?
- Did it judge value, ROI, pilot, or risk responses correctly?

Notes:

## Discovery-Question Detection

- Did the model notice when discovery was strong?
- Did it penalize calls with shallow or missing discovery?
- Were missed questions useful?

Notes:

## Closing and Follow-Up Detection

- Did the model detect clear next steps?
- Did it penalize vague endings?
- Did it mention owner, timing, and action quality?

Notes:

## Suggested Improvements

- Were suggestions practical?
- Were better example responses realistic?
- Did the model avoid generic coaching advice?

Notes:

## Turkish and English Understanding

- English transcript quality:
- Turkish transcript quality:
- Mixed-language handling:

Notes:

## Report Readability

- Is the summary clear?
- Would a salesperson understand the feedback?
- Is the tone direct but useful?

Notes:

## Overall Recommendation

- Recommended default `OLLAMA_MODEL`:
- Why:
- Concerns:
- Next test:

