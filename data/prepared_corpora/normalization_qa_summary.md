# Team Corpus QA Summary

- Input file: `/Users/aryankapadia/Downloads/q1_corpus_final.xlsx`
- Total rows: `103`
- Original query counts: `{'q1': 22, 'q2': 20, 'q3': 21, 'q4': 21, 'q5': 19}`
- Predicted query counts after normalization: `{'q1': 18, 'q3': 24, 'unknown': 4, 'q5': 15, 'q4': 20, 'q2': 22}`
- Quality decisions: `{'review': 1, 'keep': 96, 'drop': 6}`

## Per-query prepared outputs

- `q1` (Student loans vs investing): `18` ready rows (`keep=17`, `review=1`), sources={'financial_media': 7, 'brand': 4, 'credentialed': 2, 'community': 5}
- `q2` (Roth IRA vs traditional 401k): `22` ready rows (`keep=22`, `review=0`), sources={'financial_media': 3, 'brand': 14, 'credentialed': 5}
- `q3` (Emergency fund vs credit card debt): `23` ready rows (`keep=23`, `review=0`), sources={'brand': 15, 'credentialed': 3, 'financial_media': 5}
- `q4` (Buy vs rent): `20` ready rows (`keep=20`, `review=0`), sources={'financial_media': 6, 'brand': 11, 'credentialed': 3}
- `q5` (Index funds vs mortgage payoff): `12` ready rows (`keep=12`, `review=0`), sources={'credentialed': 2, 'brand': 7, 'financial_media': 3}

## Main quality issues found

- The workbook is not actually `q1` only; it contains articles for `q1` through `q5`.
- Many rows from later queries were missing IDs and used a generic `website` source type.
- A few rows are low quality for EPIC input, especially broken pages or generic subreddit/wiki pages.
- One `q1` row had a non-URL title in the `url` column, so that row is marked for review.