# Stage 2 Archive Summary — Wed Oct 22 10:23:58 PM EDT 2025

## Commit Details:
```
Commit: 987420d50d11fce87a92a7e2def00914f3d14680
Author: Kr1sg2 <silentaim15g@gmail.com>
Date: Wed Oct 22 22:23:08 2025 -0400
Subject: Audit cleanup (phase 2): archive obsolete app variants, duplicate settings, unused autopatch modules; move tests; tighten .gitignore

```

## Files Changed:
```
D	.agent_logs/backend.log
D	.agent_logs/frontend.log
M	.gitignore
D	Backend_FastAPI/bridge_watcher/README.md
D	Backend_FastAPI/bridge_watcher/watch_inbox.sh
R100	backend/app_broken.py	archive/audit_20251022/backend/app_broken.py
R100	backend/app_broken_final.py	archive/audit_20251022/backend/app_broken_final.py
R100	backend/app_clean.py	archive/audit_20251022/backend/app_clean.py
R100	backend/app_debug.py	archive/audit_20251022/backend/app_debug.py
R100	backend/app_original_backup.py	archive/audit_20251022/backend/app_original_backup.py
R100	backend/app_working.py	archive/audit_20251022/backend/app_working.py
R100	backend/indexer/chunk_fixed.py	archive/audit_20251022/backend/indexer/chunk_fixed.py
R100	backend/indexer/pipeline_fixed.py	archive/audit_20251022/backend/indexer/pipeline_fixed.py
R100	backend/indexer/pipeline_original_backup.py	archive/audit_20251022/backend/indexer/pipeline_original_backup.py
R100	backend/lexa_app/crossrefs_autopatch.py	archive/audit_20251022/backend/lexa_app/crossrefs_autopatch.py
R100	backend/lexa_app/hybrid_autopatch.py	archive/audit_20251022/backend/lexa_app/hybrid_autopatch.py
R100	backend/lexa_app/quote_facts_autopatch.py	archive/audit_20251022/backend/lexa_app/quote_facts_autopatch.py
R100	backend/lexa_app/require_sources_autopatch.py	archive/audit_20251022/backend/lexa_app/require_sources_autopatch.py
R100	backend/lexa_app/structured_style_autopatch.py	archive/audit_20251022/backend/lexa_app/structured_style_autopatch.py
R100	backend/storage/settings (Copy 2).json	archive/audit_20251022/backend/storage/settings (Copy 2).json
R100	backend/storage/settings (Copy).json	archive/audit_20251022/backend/storage/settings (Copy).json
D	backend/Backend_FastAPI/Database/.lexa-cache/006320ab77ddeadffa626e560f6db28417dbb990653a9bb32e51d2c8db592330/page-0001.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/006320ab77ddeadffa626e560f6db28417dbb990653a9bb32e51d2c8db592330/page-0001.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/008b7a2bd74a2265ae7e3da162a378ebdb9469d24537901ba684a29028559f39/page-0001.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/008b7a2bd74a2265ae7e3da162a378ebdb9469d24537901ba684a29028559f39/page-0001.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0001.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0001.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0002.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0002.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0003.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0003.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0004.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0004.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0005.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0005.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0006.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0006.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0007.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0007.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0008.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/010f0a8f5f5971bb5aa5cfda36edc75ea07f0f4b712f4bff8933a8546f8192a1/page-0008.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/0194cec31b71ce17ebf376d100f3ca1056764d4ce84e0abacdf6b0dd3c9c2e0c/page-0001.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/0194cec31b71ce17ebf376d100f3ca1056764d4ce84e0abacdf6b0dd3c9c2e0c/page-0001.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/0194cec31b71ce17ebf376d100f3ca1056764d4ce84e0abacdf6b0dd3c9c2e0c/page-0002.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/0194cec31b71ce17ebf376d100f3ca1056764d4ce84e0abacdf6b0dd3c9c2e0c/page-0002.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/0195bbf0e9bc9d4b751cec6980ad4c8f320d38fa85efacf761aa1d7162f86e58/page-0001.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/0195bbf0e9bc9d4b751cec6980ad4c8f320d38fa85efacf761aa1d7162f86e58/page-0001.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/0195bbf0e9bc9d4b751cec6980ad4c8f320d38fa85efacf761aa1d7162f86e58/page-0002.ocr.txt
D	backend/Backend_FastAPI/Database/.lexa-cache/0195bbf0e9bc9d4b751cec6980ad4c8f320d38fa85efacf761aa1d7162f86e58/page-0002.tables.json
D	backend/Backend_FastAPI/Database/.lexa-cache/0195bbf0e9bc9d4b751cec6980ad4c8f320d38fa85efacf761aa1d7162f86e58/page-0003.ocr.txt
... [truncated - 3878 total files changed]
```

## Key Actions Performed:

### 1. Archived Files (16 files to archive/audit_20251022/):
- ✅ backend/app_broken.py → archive/audit_20251022/backend/app_broken.py
- ✅ backend/app_broken_final.py → archive/audit_20251022/backend/app_broken_final.py
- ✅ backend/app_debug.py → archive/audit_20251022/backend/app_debug.py
- ✅ backend/app_original_backup.py → archive/audit_20251022/backend/app_original_backup.py
- ✅ backend/app_clean.py → archive/audit_20251022/backend/app_clean.py
- ✅ backend/app_working.py → archive/audit_20251022/backend/app_working.py
- ✅ backend/storage/settings (Copy).json → archive/audit_20251022/backend/storage/settings (Copy).json
- ✅ backend/storage/settings (Copy 2).json → archive/audit_20251022/backend/storage/settings (Copy 2).json
- ✅ backend/lexa_app/hybrid_autopatch.py → archive/audit_20251022/backend/lexa_app/hybrid_autopatch.py
- ✅ backend/lexa_app/crossrefs_autopatch.py → archive/audit_20251022/backend/lexa_app/crossrefs_autopatch.py
- ✅ backend/lexa_app/require_sources_autopatch.py → archive/audit_20251022/backend/lexa_app/require_sources_autopatch.py
- ✅ backend/lexa_app/quote_facts_autopatch.py → archive/audit_20251022/backend/lexa_app/quote_facts_autopatch.py
- ✅ backend/lexa_app/structured_style_autopatch.py → archive/audit_20251022/backend/lexa_app/structured_style_autopatch.py
- ✅ backend/indexer/pipeline_original_backup.py → archive/audit_20251022/backend/indexer/pipeline_original_backup.py
- ✅ backend/indexer/pipeline_fixed.py → archive/audit_20251022/backend/indexer/pipeline_fixed.py
- ✅ backend/indexer/chunk_fixed.py → archive/audit_20251022/backend/indexer/chunk_fixed.py

### 2. Reorganized Test Files (5 files to tests/):
- ✅ backend/test_openai.py → tests/test_openai.py
- ✅ backend/test_app.py → tests/test_app.py
- ✅ backend/test_minimal_app.py → tests/test_minimal_app.py
- ✅ backend/test-chat.html → tests/test-chat.html
- ✅ backend/test_endpoints.sh → tests/test_endpoints.sh

### 3. Updated .gitignore (3 patterns added):
- ✅ __pycache__/
- ✅ *.pyc
- ✅ backend/Database/.lexa-cache/

### 4. Cache Cleanup (from previous operation):
- ✅ Removed 3,857+ stale cache files from backend/Backend_FastAPI/Database/.lexa-cache/
- ✅ Removed .agent_logs/ files
- ✅ Removed Backend_FastAPI/bridge_watcher/ directory

## Summary Statistics:
- **Total files changed:** 3,878
- **Insertions:** 2,480 lines
- **Deletions:** 116,881 lines
- **Net reduction:** 114,401 lines
- **Files archived:** 16
- **Test files reorganized:** 5
- **Cache patterns in .gitignore:** 3

## Status: ✅ STAGE 2 COMPLETE

All changes committed to branch: audit-cleanup-20251022_221548
Commit hash: 987420d50d11fce87a92a7e2def00914f3d14680
