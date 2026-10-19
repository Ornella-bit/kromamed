"""Génère la carte d'étalonnage à imprimer (PNG).  python scripts/make_card.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2
from kromamed.card import render_card
from kromamed.color import linear_to_srgb

out = Path("out"); out.mkdir(exist_ok=True)
img = render_card(with_strip=False)           # carte seule, sans bandelette
img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
bgr = cv2.cvtColor((linear_to_srgb(img) * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
cv2.imwrite(str(out / "carte_etalonnage.png"), bgr)
print("Carte écrite :", out / "carte_etalonnage.png", "(imprimer en 100 %, papier blanc mat)")
