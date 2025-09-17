import json
import os
from typing import List, Dict

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'guild_config.json')

_default: Dict[str, Dict[str, List[int]]] = {}


def _ensure_dir():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, exist_ok=True)


def _load() -> Dict[str, Dict[str, List[int]]]:
    _ensure_dir()
    if not os.path.isfile(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save(cfg: Dict[str, Dict[str, List[int]]]):
    _ensure_dir()
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_roles(guild_id: int, key: str) -> List[int]:
    cfg = _load()
    g = cfg.get(str(guild_id), {})
    return list(map(int, g.get(key, [])))


def set_roles(guild_id: int, key: str, role_ids: List[int]):
    cfg = _load()
    g = cfg.setdefault(str(guild_id), {})
    g[key] = list(map(int, role_ids))
    _save(cfg)


def get_moderator_roles(guild_id: int) -> List[int]:
    return get_roles(guild_id, 'moderator_roles')


def set_moderator_roles(guild_id: int, role_ids: List[int]):
    set_roles(guild_id, 'moderator_roles', role_ids)


def get_music_roles(guild_id: int) -> List[int]:
    return get_roles(guild_id, 'music_roles')


def set_music_roles(guild_id: int, role_ids: List[int]):
    set_roles(guild_id, 'music_roles', role_ids)
