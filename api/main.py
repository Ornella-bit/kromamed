"""
API KromaMed (Livraison 2) : met le moteur de vision à disposition par Internet.

Lancer en local :   uvicorn api.main:app --reload
Puis ouvrir        :   http://127.0.0.1:8000        (page de démo)
Documentation auto :   http://127.0.0.1:8000/docs   (Swagger, généré par FastAPI)

Routes
    GET  /api/health            -> {"status": "ok"}
    GET  /api/scenarios         -> liste des photos de démonstration
    GET  /api/demo/{scenario}   -> fabrique une photo simulée, l'analyse, renvoie tout
    POST /api/analyze           -> analyse la photo envoyée (champ "file")

Confidentialité : l'image reçue est analysée en mémoire puis oubliée. Rien n'est écrit sur disque.
"""
from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from kromamed import __version__, analyze
from kromamed import config as C
from .exports import build_history_xlsx
from .report import build_report_pdf
from kromamed.pipeline import AnalysisResult
from kromamed.simulate import simulate_photo

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"

MAX_UPLOAD_BYTES = 12 * 1024 * 1024     # 12 Mo
MAX_SIDE = 2400                         # px : on réduit les photos plus grandes (vitesse)

app = FastAPI(
    title="KromaMed API",
    version=__version__,
    description="Lecture colorimétrique de bandelettes urinaires. Aide à la lecture, pas un diagnostic.",
)
# Ouvert à tous pour permettre à une future app mobile d'appeler l'API (pas de cookies ici).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


# ------------------------------------------------------------ scénarios --
_NORMAL = C.NORMAL_DEFAULT

SCENARIOS: dict[str, dict] = {
    "sain": dict(label="Résultat normal", levels=_NORMAL, kwargs={}),
    "proteinurie": dict(label="Protéinurie (risque pré-éclampsie)",
                        levels={**_NORMAL, "proteines": "++"}, kwargs={}),
    "infection": dict(label="Infection urinaire probable",
                      levels={**_NORMAL, "leucocytes": "++", "nitrites": "positif", "sang": "+"}, kwargs={}),
    "diabete": dict(label="Glycosurie et cétonurie",
                    levels={**_NORMAL, "glucose": "+++", "cetones": "+"}, kwargs={}),
    "hepatique": dict(label="Bilirubine et urobilinogène élevés",
                      levels={**_NORMAL, "bilirubine": "++", "urobilinogene": "++"}, kwargs={}),
    "lumiere_chaude": dict(label="Éclairage jaune et ombre (corrigé)",
                           levels={**_NORMAL, "proteines": "+"},
                           kwargs=dict(warm=0.45, shadow=0.12)),
    "flou": dict(label="Photo floue (doit être refusée)", levels=_NORMAL, kwargs=dict(blur_sigma=2.5)),
    "ombre_forte": dict(label="Ombre trop forte (doit être refusée)", levels=_NORMAL, kwargs=dict(shadow=0.75)),
    "repere_cache": dict(label="Repère de la carte caché (doit être refusée)", levels=_NORMAL,
                         kwargs=dict(hide_marker=1)),
}

PARAM_LABELS = C.LABELS_FR


# ----------------------------------------------------------------- outils --
def _data_url(img_bgr: np.ndarray, max_width: int = 900, quality: int = 85) -> str:
    h, w = img_bgr.shape[:2]
    if w > max_width:
        img_bgr = cv2.resize(img_bgr, (max_width, int(h * max_width / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def _summary(res: AnalysisResult) -> dict:
    """Phrases lisibles pour l'écran (en français)."""
    if res.status != "ok":
        return {"headline": "Analyse refusée : refaire la photo",
                "details": res.quality.reasons or ["Photo inexploitable."],
                "level": "rejected"}
    abnormal = [f"{PARAM_LABELS[p.param]} : {p.level}" for p in res.pads if p.normal is False]
    unsure = [PARAM_LABELS[p.param] for p in res.pads if p.status != "ok"]
    if unsure:
        return {"headline": "Résultat incomplet",
                "details": [f"Lecture incertaine pour : {', '.join(unsure)}. Refaire la photo."]
                          + ([f"Valeurs anormales : {', '.join(abnormal)}."] if abnormal else []),
                "level": "warn"}
    if abnormal:
        return {"headline": "Anomalie(s) détectée(s)",
                "details": abnormal + ["À confirmer par un professionnel de santé."], "level": "alert"}
    return {"headline": "Aucune anomalie détectée", "details": ["Tous les paramètres sont dans la norme."],
            "level": "ok"}


def _response(res: AnalysisResult, input_img: np.ndarray) -> dict:
    out = res.to_dict()
    out["summary"] = _summary(res)
    for p in out["pads"]:
        p["label"] = PARAM_LABELS[p["param"]]
        p["read_time_s"] = C.READ_TIME_S[p["param"]]
    images = {"input": _data_url(input_img)}
    for key in ("card_raw", "card_corrected", "card_result"):
        if key in res.debug:
            images[key] = _data_url(res.debug[key], max_width=600)
    out["images"] = images
    out["disclaimer"] = "Aide à la lecture, pas un diagnostic médical."
    out["brand"] = C.BRAND
    return out


def _decode(data: bytes) -> np.ndarray:
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)   # applique l'orientation EXIF
    if img is None:
        raise HTTPException(status_code=400, detail="Fichier illisible : envoyer une photo JPG ou PNG.")
    h, w = img.shape[:2]
    if max(h, w) > MAX_SIDE:
        s = MAX_SIDE / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img


# ----------------------------------------------------------------- routes --
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/scenarios")
def scenarios() -> list[dict]:
    return [{"id": k, "label": v["label"]} for k, v in SCENARIOS.items()]


@app.get("/api/demo/{scenario}")
def demo(scenario: str) -> dict:
    spec = SCENARIOS.get(scenario)
    if spec is None:
        raise HTTPException(status_code=404, detail="Scénario inconnu.")
    img = simulate_photo(spec["levels"], seed=42, **spec["kwargs"])
    return _response(analyze(img, keep_debug=True), img)


@app.post("/api/analyze")
def analyze_upload(file: UploadFile = File(...)) -> dict:
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Photo trop lourde (12 Mo maximum).")
    img = _decode(data)
    return _response(analyze(img, keep_debug=True), img)


class ReportRequest(BaseModel):
    patient_id: str = Field(default="", max_length=60)
    date: str | None = Field(default=None, max_length=40)
    result: dict


class HistoryRequest(BaseModel):
    rows: list[dict] = Field(max_length=2000)


@app.post("/api/report")
def report(req: ReportRequest) -> Response:
    """PDF du rapport. Le résultat est renvoyé par le navigateur : rien n'est stocké côté serveur."""
    r = req.result
    if r.get("status") != "ok" or "pads" not in r or "quality" not in r:
        raise HTTPException(status_code=422, detail="Aucun résultat valide à mettre en rapport.")
    pdf = build_report_pdf(req.patient_id.strip(), req.date, r)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="rapport_kromamed.pdf"'})


@app.post("/api/history/xlsx")
def history_xlsx(req: HistoryRequest) -> Response:
    """Excel de l'historique (colonnes de base_donnees_tests.xlsx). Historique gardé dans le navigateur."""
    data = build_history_xlsx(req.rows)
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="historique_kromamed.xlsx"'})


# --------------------------------------------------------------- site web --
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(WEB / "index.html")
