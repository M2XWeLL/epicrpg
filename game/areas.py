import json
from pathlib import Path
import config

_data = None


def load_areas() -> dict:
    global _data
    if _data is None:
        path = config.DATA_DIR / "areas.json"
        with open(path, "r", encoding="utf-8") as f:
            _data = json.load(f)
    return _data["areas"]


def get_area(area_num: int) -> dict | None:
    areas = load_areas()
    return areas.get(str(area_num))


def can_enter_area(level: int, area: int) -> bool:
    a = get_area(area)
    if not a:
        return False
    return level >= a["min_level"]


def get_next_area_requirement(current_area: int) -> dict | None:
    next_area = get_area(current_area + 1)
    if not next_area:
        return None
    return {
        "area": current_area + 1,
        "name": next_area["name"],
        "min_level": next_area["min_level"],
    }


def get_area_drops(area_num: int) -> list:
    area = get_area(area_num)
    if not area:
        return []
    return area.get("drops", [])
