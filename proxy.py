import os, requests, time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# --- Agri portaali API ---
AGRI_API = "https://portaal.agri.ee/api/public/ppp/plantprotectionproduct"
TIMEOUT = 20

# --- Väike vahemälu, et kiirendada kordusküsimusi ---
CACHE_TTL = 60  # sekundites
_cache = {}

app = FastAPI(title="Agri Proxy")

# --- Lubame GPT ja teiste väliste domeenide päringud ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/taimekaitse")
def taimekaitse(query: str = Query(..., min_length=1, max_length=200)):
    """
    Vahendab päringut Agri API-le.
    Seda kasutatakse ChatGPT Custom GPT Actioni kaudu,
    et saada ametlikke andmeid taimekaitsevahendite kohta.
    """
    q = query.strip()
    now = time.time()

    # --- Vahemälu kontroll ---
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
        _cache[q] = (now, data)
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Agri API viga: {e}")
    except ValueError:
        raise HTTPException(status_code=500, detail="JSON parsimise viga Agri vastuses")
