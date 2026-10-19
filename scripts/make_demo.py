"""Crée data/demo/photo_demo.png (photo simulée : protéines ++ et glucose +)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2
from kromamed import config as C
from kromamed.simulate import simulate_photo

levels = {**C.NORMAL_DEFAULT, "proteines": "++", "glucose": "+"}
Path("data/demo").mkdir(parents=True, exist_ok=True)
cv2.imwrite("data/demo/photo_demo.png", simulate_photo(levels, seed=42))
print("data/demo/photo_demo.png créée")
