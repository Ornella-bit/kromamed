"""
Génère la carte d'étalonnage à imprimer.
    python scripts/make_card.py
Écrit out/carte_etalonnage.png et out/carte_etalonnage_A4.pdf (carte de 150 x 225 mm, taille réelle).
IMPRIMER À 100 % (« taille réelle », jamais « ajuster à la page »), sur papier blanc mat.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from kromamed import config as C
from kromamed.card import render_card
from kromamed.color import linear_to_srgb

out = Path("out"); out.mkdir(exist_ok=True)
img = render_card(with_strip=False)                       # carte seule, sans bandelette
img = cv2.resize(img, None, fx=5, fy=5, interpolation=cv2.INTER_NEAREST)
bgr = cv2.cvtColor((linear_to_srgb(img) * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
png = out / "carte_etalonnage.png"
cv2.imwrite(str(png), bgr)

w_mm, h_mm = C.CARD_W / C.PX_PER_MM, C.CARD_H / C.PX_PER_MM        # 150 x 225 mm
pdf = out / "carte_etalonnage_A4.pdf"
c = canvas.Canvas(str(pdf), pagesize=A4)
x, y = (A4[0] - w_mm * mm) / 2, (A4[1] - h_mm * mm) / 2 + 4 * mm
c.drawImage(str(png), x, y, w_mm * mm, h_mm * mm)
c.setFont("Helvetica", 8)
c.drawCentredString(A4[0] / 2, 9 * mm, f"KromaMed - carte {w_mm:.0f} x {h_mm:.0f} mm - imprimer a 100 % (taille reelle), papier blanc mat")
c.showPage(); c.save()
print("PNG :", png)
print("PDF :", pdf, f"(carte de {w_mm:.0f} x {h_mm:.0f} mm : verifier avec une regle apres impression)")
