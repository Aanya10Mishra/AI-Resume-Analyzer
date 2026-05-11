# Human Evaluation Pack

This folder is designed to mirror the Google Sheet workflow:

- `evaluator1.csv`
- `evaluator2.csv`
- `evaluator3.csv`
- `rubric.csv`
- `system_scores.csv`
- `sample_filled_evaluator.csv`

## How to use it

1. Upload each evaluator CSV into a separate Google Sheet tab.
2. Recommended tab names:
   - `Evaluator 1`
   - `Evaluator 2`
   - `Evaluator 3`
   - `Rubric`
3. Keep `pair_id`, `job_role`, and `resume_snippet` unchanged.
4. Ask evaluators to fill only:
   - `skill`
   - `experience`
   - `overall`
   - `notes`
5. Export each tab back to CSV with the same filenames.
6. Run:

```powershell
python compute_irr.py
```

The script prints `[PAPER]` lines you can paste into your methodology or results section.
