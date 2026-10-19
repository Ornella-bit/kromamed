"""
Analyse une photo et affiche le résultat.
    python scripts/run.py data/demo/photo_demo.png --out out
Écrit out/resultat.json et des images de contrôle (carte redressée, résultat annoté).
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2
from kromamed import analyze

ap = argparse.ArgumentParser()
ap.add_argument("image")
ap.add_argument("--out", default="out")
args = ap.parse_args()

res = analyze(args.image, keep_debug=True)
out = Path(args.out); out.mkdir(exist_ok=True, parents=True)
(out / "resultat.json").write_text(json.dumps(res.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
for name, img in res.debug.items():
    cv2.imwrite(str(out / f"{name}.png"), img)

q = res.quality
print(f"Qualité globale : {q.overall:.0%}  (seuil 85 %)")
if res.status != "ok":
    print("ANALYSE REFUSÉE - nouvelle photo nécessaire :")
    for r in q.reasons:
        print("  -", r)
else:
    for p in res.pads:
        niveau = p.level or "indéterminé"
        print(f"  {p.param:11s} {niveau:12s} (confiance {p.confidence:.0%}, ΔE {p.delta_e:.1f})")
    print("Verdict :", {True: "aucune anomalie", False: "anomalie(s) détectée(s)", None: "incomplet"}[res.all_normal])
print(f"Temps : {res.duration_ms:.0f} ms  -> fichiers dans {out}/")
