import os, requests, time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

AGRI_API = "https://portaal.agri.ee/api/public/ppp/plantprotectionproduct"
TIMEOUT = 20

# lihtne mälupuhver (60 s) – vähendab koormust ja kiirendab kordusküsimusi
CACHE_TTL = 60
_cache = {}  # key: query string -> (timestamp, data)

app = FastAPI(title="Agri proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # GPT pärit erinevatest domeenidest
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/taimekaitse")
def taimekaitse(query: str = Query(..., min_length=1, max_length=200)):
    q = query.strip()
    now = time.time()

    if q in _cache and now - _cache[q][0] < CACHE_TTL:
        return _cache[q][1]

    try:
        r = requests.get(
            AGRI_API,
            params={"query": q},
            headers={"User-Agent": "AgriProxy/1.0 (+education)"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        # lihtne kuju ühtlustus: tagastame vaid vajaliku (aga jätame originaali struktuuri alles)
        _cache[q] = (now, data)
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Agri API viga: {e}")
    except ValueError:
        raise HTTPException(status_code=500, detail="JSON parsimise viga Agri vastuses")