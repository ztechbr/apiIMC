#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from geoip2.database import Reader
from geoip2.errors import AddressNotFoundError

app = FastAPI(
    title="API IMC",
    description="API para classificação de IMC",
    version="1.0.0",
)

# =========================
# Arquivo de log do honeypot
# =========================
BLOCKED_LOG = Path("blocked_ips.json")
GEOIP_DB = Path("GeoLite2-City.mmdb")

geo_reader = Reader(str(GEOIP_DB)) if GEOIP_DB.exists() else None

# =========================
# Segurança – padrões óbvios de scan
# =========================
SUSPICIOUS_PATTERNS = re.compile(
    r"(wp-|\.env|\.git|phpinfo|cmd=|exec=|shell=|command=|/etc/passwd|\.aws)",
    re.IGNORECASE
)

# =========================
# Enriquecimento GeoIP
# =========================
def geoip_lookup(ip: str) -> dict:
    if not geo_reader:
        return {}

    try:
        r = geo_reader.city(ip)
        return {
            "country": r.country.name,
            "country_iso": r.country.iso_code,
            "city": r.city.name,
            "latitude": r.location.latitude,
            "longitude": r.location.longitude,
            "asn": r.traits.autonomous_system_number,
            "org": r.traits.autonomous_system_organization,
        }
    except AddressNotFoundError:
        return {}
    except Exception:
        return {}

# =========================
# Registro de bloqueio
# =========================
def log_blocked_request(request: Request):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "ip": ip,
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query,
        "user_agent": ua,
        "headers": {
            "referer": request.headers.get("referer"),
            "x-forwarded-for": request.headers.get("x-forwarded-for"),
        },
        "geo": geoip_lookup(ip),
    }

    # grava em JSON (uma linha por evento)
    with BLOCKED_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # log no console
    print("[BLOCKED]", json.dumps(entry, ensure_ascii=False))

# =========================
# Middleware – bloqueia e registra
# =========================
@app.middleware("http")
async def block_scanners(request: Request, call_next):
    target = str(request.url)

    if SUSPICIOUS_PATTERNS.search(target):
        log_blocked_request(request)
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    return await call_next(request)

# =========================
# Headers de segurança
# =========================
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

# =========================
# Regras de domínio
# =========================
def classificar_imc(imc: float) -> dict:
    if imc < 18.5:
        return {"classificacao": "Magreza", "obesidade_grau": 0}
    elif 18.5 <= imc <= 24.9:
        return {"classificacao": "Normal", "obesidade_grau": 0}
    elif 25.0 <= imc <= 29.9:
        return {"classificacao": "Sobrepeso", "obesidade_grau": 1}
    elif 30.0 <= imc <= 39.9:
        return {"classificacao": "Obesidade", "obesidade_grau": 2}
    else:
        return {"classificacao": "Obesidade Grave", "obesidade_grau": 3}

# =========================
# Validação estrita
# =========================
def only_valor(valor: float = Query(..., gt=0, le=200)):
    return valor

# =========================
# Endpoints
# =========================
@app.get("/")
async def root(request: Request):
    if request.query_params:
        raise HTTPException(status_code=404)
    return {
        "mensagem": "API de Classificação de IMC",
        "endpoint": "/imc?valor=<numero>",
        "exemplo": "/imc?valor=25.5"
    }

@app.get("/imc")
async def calcular_imc(valor: float = Depends(only_valor)):
    return {"imc": valor, **classificar_imc(valor)}

@app.get("/health")
async def health_check(request: Request):
    if request.client.host != "127.0.0.1":
        raise HTTPException(status_code=404)
    return {"status": "ok"}

# =========================
# Bloqueio explícito de métodos não usados
# =========================
@app.api_route("/{path:path}", methods=["POST", "PUT", "DELETE", "PATCH", "HEAD"])
async def method_not_allowed(request: Request):
    log_blocked_request(request)
    return Response(status_code=404)

# =========================
# Bootstrap
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5600,
        log_level="warning"
    )


