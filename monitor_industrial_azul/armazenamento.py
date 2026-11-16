import csv
from pathlib import Path
from datetime import datetime
def save_measurement(level,pct,source,arduino_distance=None):
    path=Path("medicoes.csv"); new=not path.exists()
    with path.open("a",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        if new: w.writerow(["data_hora","nivel_visual_cm","percentual","origem","distancia_arduino_cm"])
        w.writerow([datetime.now().isoformat(timespec="seconds"),
                    "" if level is None else round(level,2),
                    "" if pct is None else round(pct,1),source,
                    "" if arduino_distance is None else round(arduino_distance,2)])
