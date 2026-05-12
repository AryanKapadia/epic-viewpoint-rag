# Submission Bundle

This folder contains the core artifacts for EPIC v4 submission.

## Structure

- `pipeline/`
  - `epistemic_rag_v4_pipeline.ipynb`
    - Main generalized EPIC v4 notebook

- `app/`
  - `streamlit_app.py`
    - Streamlit interface for displaying the final viewpoints
  - The app supports both the original project layout and this submission-bundle layout.

- `data/raw_documents/`
  - `q1_corpus_final.xlsx`
    - Original mixed workbook provided during corpus collection

- `data/prepared_corpora/`
  - `q1_corpus_prepared.xlsx`
  - `q2_corpus_prepared.xlsx`
  - `q3_corpus_prepared.xlsx`
  - `q4_corpus_prepared.xlsx`
  - `q5_corpus_prepared.xlsx`
  - `team_corpus_normalized_master.xlsx`
  - `normalization_qa_summary.md`
  - `normalization_qa_summary.json`
    - Cleaned and query-split corpora used by EPIC v4

- `runs/`
  - all saved EPIC v4 run directories under `epistemic-rag/data_v4/`
  - this includes:
    - `q1_topk5`, `q1_topk10`, `q1_topk15`, `q1_topk20`, `q1_topk50`
    - `q2_topk5`, `q2_topk10`, `q2_topk15`, `q2_topk20`, `q2_topk50`
    - `q3_topk5`, `q3_topk10`, `q3_topk15`, `q3_topk20`
    - `q4_topk5`, `q4_topk10`, `q4_topk15`, `q4_topk20`
    - `q5_topk5`, `q5_topk10`, `q5_topk15`, `q5_topk20`

## Note on report-highlighted runs

Although the bundle now contains all saved runs, the report primarily highlights:

- `q1_topk15`
- `q2_topk15`
- `q3_topk15`
- `q4_topk20`
- `q5_topk15`

because these were the most representative qualitative runs used in the write-up.

## Key files inside each run directory

Each run directory contains the saved artifacts for that run, including:

- `retrieved_docs.json`
- `structured_arguments.json`
- `structured_scored.json`
- `arguments_indexed.json`
- `claim_embeddings.npy`
- `support_embeddings.npy`
- `perspective_clusters.json`
- `perspective_summaries.json`
- `final_output.json`
- `main_viewpoints.json`
- `evaluation.json`
- `step_times.json`

## Notes

- The prepared corpora in `data/prepared_corpora/` are the intended EPIC v4 inputs.
- The original workbook in `data/raw_documents/` is included for completeness.
- The `runs/` directory contains the final saved outputs used for analysis and reporting.

## Deployment

For a simple public demo:

1. Push this folder to GitHub.
2. Point Streamlit Community Cloud to `app/streamlit_app.py`.
3. Use `requirements.txt` in the bundle root for installation.

The app only reads saved run artifacts; it does not need to rerun the full EPIC pipeline to display results.
