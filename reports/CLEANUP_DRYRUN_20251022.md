# Cleanup Dry-Run Report - Lexa AI V2
**Generated:** Wed Oct 22 10:19:11 PM EDT 2025
**Branch:** audit-cleanup-20251022_221548

## 📊 Executive Summary

- ✅ **Total files to archive:** 16 files
- ✅ **Space to recover:** ~262 KB from obsolete code
- ✅ **Risk level:** **LOW** - No active code references archived files

## 📁 Files Verified for Archival

- ✅ `backend/app_broken.py` - 9711 bytes (298 lines)
- ✅ `backend/app_broken_final.py` - 9611 bytes (291 lines)
- ✅ `backend/app_debug.py` - 75133 bytes (1928 lines)
- ✅ `backend/app_original_backup.py` - 75133 bytes (1928 lines)
- ✅ `backend/app_clean.py` - 8022 bytes (254 lines)
- ✅ `backend/app_working.py` - 348 bytes (12 lines)
- ✅ `backend/storage/settings (Copy).json` - 9492 bytes (151 lines)
- ✅ `backend/storage/settings (Copy 2).json` - 9492 bytes (151 lines)
- ✅ `backend/lexa_app/hybrid_autopatch.py` - 8516 bytes (220 lines)
- ✅ `backend/lexa_app/crossrefs_autopatch.py` - 3974 bytes (112 lines)
- ✅ `backend/lexa_app/require_sources_autopatch.py` - 1983 bytes (59 lines)
- ✅ `backend/lexa_app/quote_facts_autopatch.py` - 3426 bytes (99 lines)
- ✅ `backend/lexa_app/structured_style_autopatch.py` - 2026 bytes (53 lines)
- ✅ `backend/indexer/pipeline_original_backup.py` - 11042 bytes (297 lines)
- ✅ `backend/indexer/pipeline_fixed.py` - 22517 bytes (566 lines)
- ✅ `backend/indexer/chunk_fixed.py` - 2933 bytes (81 lines)

## 🔍 Import Analysis - Autopatch Modules

```
No imports found - SAFE TO ARCHIVE ✅
```

## 🔍 Langchain Usage Analysis

```
backend/app_debug.py:from langchain_openai import OpenAIEmbeddings
backend/app_debug.py:from langchain.text_splitter import RecursiveCharacterTextSplitter
backend/app_original_backup.py:from langchain_openai import OpenAIEmbeddings
backend/app_original_backup.py:from langchain.text_splitter import RecursiveCharacterTextSplitter
```
**Result:** Langchain ONLY used in app_debug.py and app_original_backup.py (both being archived)
