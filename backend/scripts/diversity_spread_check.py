from pprint import pprint
import sys

sys.path.insert(0, ".")
try:
    # Try enhanced API
    from lexa_app.retrieval import enhanced_search as fn

    def call(q, k=6):
        return fn(q, k)

except Exception:
    try:
        # Fallback to engine
        from lexa_app.retrieval import RetrievalEngine

        engine = RetrievalEngine()

        def call(q, k=6):
            return engine.retrieve_with_rerank(q, final_k=k)

    except Exception:
        try:
            # Try direct function
            from lexa_app.retrieval import retrieve_chunks

            def call(q, k=6):
                return retrieve_chunks(q, k=k)

        except Exception:
            from lexa_app.retrieval import retrieve

            def call(q, k=6):
                return retrieve(q, k)


for q in [
    "how do I fix minor scratches on rattan",
    "touch-up supply request form",
    "what is our PTO policy",
]:
    try:
        res = call(q, k=6)
        spread = []
        for r in res:
            md = r.get("metadata", {}) if isinstance(r, dict) else {}
            if isinstance(md, list) and md:
                md = md[0]
            spread.append(
                (
                    md.get("doc_filename")
                    or md.get("file_name")
                    or md.get("source")
                    or md.get("doc_name"),
                    md.get("page_start")
                    or md.get("page")
                    or md.get("page_no")
                    or md.get("page_number"),
                    md.get("page_end"),
                    md.get("chunk_type"),
                )
            )
        print("\nQ:", q)
        pprint(spread)
    except Exception as e:
        print(f"\nError for '{q}': {e}")
