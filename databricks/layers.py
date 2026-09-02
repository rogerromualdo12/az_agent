from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BRONZE = DATA_DIR / "bronze"
SILVER = DATA_DIR / "silver"
GOLD = DATA_DIR / "gold"
PLOTS_DIR = GOLD / "plots"


def ensure_layers() -> None:
    for path in (BRONZE, SILVER, GOLD, PLOTS_DIR):
        path.mkdir(parents=True, exist_ok=True)
