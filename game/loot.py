import random
import json
from pathlib import Path
import config


def get_lootbox_rewards(lootbox_type: str = "common") -> dict:
    """Roll lootbox contents."""
    rewards = {"coins": 0, "materials": {}, "items": []}

    if lootbox_type == "common":
        rewards["coins"] = random.randint(50, 200)
        if random.random() < 0.3:
            rewards["materials"]["iron"] = random.randint(1, 3)
        if random.random() < 0.1:
            rewards["materials"]["ruby"] = random.randint(1, 2)
        if random.random() < 0.5:
            rewards["materials"]["wood"] = random.randint(5, 15)
    elif lootbox_type == "rare":
        rewards["coins"] = random.randint(200, 800)
        if random.random() < 0.4:
            rewards["materials"]["iron"] = random.randint(5, 10)
        if random.random() < 0.2:
            rewards["materials"]["ruby"] = random.randint(2, 5)

    return rewards
