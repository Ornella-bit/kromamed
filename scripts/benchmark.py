"""
Benchmark Phase 1 : 100 photos simulées aléatoires (éclairages, ombres,
teintes, perspectives, niveaux différents) + cas dégradés qui DOIVENT être refusés.

Usage :  python scripts/benchmark.py [--n 100]
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from kromamed import analyze
from kromamed import config as C
from kromamed.simulate import simulate_photo, random_levels


def main(n: int) -> int:
    rng = np.random.default_rng(2026)
    ok = rejected = pad_total = pad_correct = pad_undecided = 0
    times = []
    errors: list[str] = []
    for i in range(n):
        levels = random_levels(rng)
        img = simulate_photo(levels, seed=i, shadow=rng.uniform(0, 0.12), warm=rng.uniform(0, 0.4))
        r = analyze(img)
        times.append(r.duration_ms)
        if r.status != "ok":
            rejected += 1
            continue
        ok += 1
        for p in r.pads:
            pad_total += 1
            if p.status != "ok":
                pad_undecided += 1
            elif p.level == levels[p.param]:
                pad_correct += 1
            else:
                errors.append(f"photo {i}: {p.param} lu {p.level} au lieu de {levels[p.param]}")

    print(f"Photos normales      : {n}  (analysées {ok}, refusées {rejected})")
    print(f"Plages lues          : {pad_total}")
    print(f"  correctes          : {pad_correct}  ({100 * pad_correct / max(pad_total, 1):.2f} %)")
    print(f"  indéterminées      : {pad_undecided}")
    print(f"  FAUSSES            : {len(errors)}")
    for e in errors[:10]:
        print("   ", e)
    print(f"Temps moyen / photo  : {np.mean(times):.0f} ms (PC, Python ; la cible mobile <1,5 s sera mesurée en Phase 2)")

    print("\nCas dégradés (doivent tous être REFUSÉS) :")
    lv = random_levels(rng)
    cases = {
        "flou fort": simulate_photo(lv, seed=1, blur_sigma=6),
        "flou léger": simulate_photo(lv, seed=2, blur_sigma=2.5),
        "repère caché": simulate_photo(lv, seed=3, hide_marker=1),
        "ombre très forte": simulate_photo(lv, seed=4, shadow=0.75),
    }
    bad = 0
    for name, img in cases.items():
        r = analyze(img)
        flag = "OK (refusée)" if r.status == "rejected" else "PROBLÈME (acceptée)"
        bad += r.status != "rejected"
        print(f"  {name:18s} -> {flag}  score={r.quality.overall:.2f}  {r.quality.reasons[:1]}")
    return 0 if (not errors and bad == 0) else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    sys.exit(main(ap.parse_args().n))
