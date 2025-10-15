from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
import json
import math
from typing import Optional

# initiation
app = FastAPI()

# allowed origins for frontend access
# add your dev urls here if you're testing locally or deploying elsewhere
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5000",
    "http://localhost:3000",
    "https://doespythonhaveit.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# loading the model
m = "all-mpnet-base-v2"
"""
Alternative models (you can experiment by switching these in 'm'):

    - all-MiniLM-L6-v2            (super fast, lightweight, surprisingly accurate, 
                                   in my quality test it even outperformed L12, but that
                                   might be dataset formatting luck, it was a bit different too back then)
    - all-MiniLM-L12-v2           (slower and heavier than L6, theoretically more precise 
                                   but didn't always beat it in real-world tests)
    - thenlper/gte-large          (high accuracy, strong general-purpose embeddings, heavier on 
                                    RAM/VRAM though)
    - multi-qa-mpnet-base-dot-v1    (optimized for question-answer retrieval tasks, great if search 
                                    queries are phrased as questions)
    - multi-qa-MiniLM-L6-cos-v1     (faster version of above, trades a bit of precision for speed)
    - paraphrase-MiniLM-L3-v2       (super tiny and blazingly fast, good for testing or mobile/edge 
                                    use, not as accurate)
    - all-distilroberta-v1          (older but still solid, performs decently for simpler           
                                    english-only sentence comparisons)

    *anyway you can also tell me if you found better models for semantic search
"""

print(m)
print("Loading model...")
model = SentenceTransformer(m)
print("Model loaded ✅")

# loading the json file
with open("libraries.json", "r", encoding="utf-8") as q:
    libraries = json.load(q)

# cleaning the format to ensure consistent keyword formats and precomputed fields
for lib in libraries:
    keywords = lib.get("keywords", [])

    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    cleaned_keywords = []
    hyphen_tags = []

    for k in keywords:
        hyphen_tags.append(k.strip())

        cleaned_keywords.append(k.replace("-", " ").strip())

    lib["keywords"] = cleaned_keywords
    lib["tags"] = hyphen_tags

    lib["_search_name"] = lib.get("name", "").lower()
    lib["_search_keywords"] = " ".join(cleaned_keywords).lower()
    lib["_search_category"] = lib.get("category", "").lower()


# precomputing
# we encode all library descriptions into embeddings once at startup
# this can take time depending on the model and number of libraries
# if you add new libraries, restart the server to regenerate embeddings
search_texts = [
    f"{lib.get('user_desc', '')}. {lib.get('search_desc', '')}. {' '.join(lib.get('keywords', []))}"
    for lib in libraries
]
print("Encoding library embeddings...")
library_embeddings = model.encode(
    search_texts, convert_to_tensor=True, show_progress_bar=True
)
print("Embeddings ready ✅")


# defining library
class Library(BaseModel):
    name: str
    category: Optional[str] = "uncategorized"
    user_desc: Optional[str] = "no description"
    search_desc: Optional[str] = ""
    keywords: Optional[list[str]] = []
    link: Optional[str] = ""


# api: search
@app.get("/search")
async def search(q: str | None = None, top_k: int = 10, threshold: float = 0.3):
    # adjust threshold or weights inside literal_score for tuning performance
    # top-k controls how many best results are returned

    try:
        if not q:
            raise HTTPException(400, detail="Please provide a query parameter 'q'")

        # normalize the query
        q_lower = q.lower().strip()
        q_variants = {
            q_lower,
            q_lower.replace("-", " "),  # make-website -> make website
            q_lower.replace(" ", "-"),  # make website -> make-website
            q_lower.replace(" ", ""),  # make website -> makewebsite
        }

        # semantic similarity
        query_embedding = model.encode(q, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, library_embeddings)[0].cpu().numpy()

        results = []

        for i, lib in enumerate(libraries):
            literal_score = 0.0

            if any(v in lib["_search_name"] for v in q_variants):
                literal_score += 0.25
            if any(v in lib["_search_category"] for v in q_variants):
                literal_score += 0.1

            if any(v in lib.get("_search_keywords", "") for v in q_variants):
                literal_score += 0.15
            if any(v in " ".join(lib.get("tags", [])).lower() for v in q_variants):
                literal_score += 0.15

            total_score = float(cos_scores[i]) + literal_score

            if total_score < threshold:
                continue

            results.append(
                {
                    "name": lib["name"],
                    "category": lib.get("category", "uncategorized"),
                    "desc": lib.get("user_desc", "no description"),
                    "link": lib.get("link", ""),
                    "score": round(total_score, 4),
                }
            )

        # sort
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

        if not results:
            return {"response": "false", "message": "No relevant results found."}

        return {"response": "true", "results": results}

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


max_limit = 60


# api: all
# basic pagination endpoint to get all libraries
# can be used by frontend or developers to browse or debug library data
# you can safely tweak pagination or add filters here
@app.get("/all")
async def all(lim: int = 10, page: int = 1):
    limit = max(1, min(lim, max_limit))
    total_results = len(libraries)
    start_index = (page - 1) * limit
    end_index = min((start_index + limit), total_results)
    total_pages = math.ceil(total_results / limit)

    has_previous = page > 1
    has_next = page < total_pages

    return {
        "page": page,
        "limit": limit,
        "total_results": total_results,
        "total_pages": total_pages,
        "has_prev": has_previous,
        "has_next": has_next,
        "results": libraries[start_index:end_index],
    }
