# OCR / Lab Report Extraction — Generations

This file tracks the versions of the OCR pipeline that have been saved under `ocr_snapshots/` so that any working state can be restored.

## Naming convention

- `ocr_snapshots/app_YYYYMMDD_HHmmss.py` — snapshot of `app.py` before a change
- `ocr_snapshots/test_ocr_live_YYYYMMDD_HHmmss.py` — snapshot of `test_ocr_live.py` before a change

The timestamp matches the moment the snapshot was taken. To restore a version, copy the snapshot back to the original filename.

## History

| Generation | Snapshot(s) | What changed |
|---|---|---|
| 1 (2026-08-24 pre-backup) | `app_20260824_20xxxx.py` | Original two-stage OCR: grayscale preprocessing, multi-pass consensus, row repair. Accuracy was 66% for the target report. |
| 2 (current) | `app_20260824_20xxxx.py` | Removed multi-pass/verify, restored single-pass default, kept colour image, strengthened repair prompt to prevent value shifting/repeating. |

## How to compare generations

1. Pick the timestamped `app_*.py` to test.
2. Temporarily replace `app.py` with the snapshot.
3. Run the live test:

```powershell
python test_ocr_live.py "health_uploaded_documents/23/20260821_115914_8a622016_image.jpg"
```

4. Restore the latest `app.py` when finished.
