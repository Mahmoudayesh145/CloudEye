import json
import os
from typing import List, Dict, Any, Optional
from url_utils import extract_folder_id

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "username": "",
    "notification_email": "",
    "folders": []
}

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "username" not in data:
                data["username"] = ""
            if "notification_email" not in data:
                data["notification_email"] = ""
            if "folders" not in data:
                data["folders"] = []
            return data
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def get_username() -> str:
    cfg = load_config()
    return cfg.get("username", "").strip()

def set_username(name: str) -> None:
    cfg = load_config()
    cfg["username"] = name.strip()
    save_config(cfg)

def set_notification_email(email: str) -> None:
    cfg = load_config()
    cfg["notification_email"] = email.strip()
    save_config(cfg)

def get_notification_email() -> str:
    cfg = load_config()
    return cfg.get("notification_email", "").strip()

def get_folders() -> List[Dict[str, Any]]:
    cfg = load_config()
    return cfg.get("folders", [])

def add_folder(name: str, url_or_id: str, default_dest: str) -> Optional[Dict[str, Any]]:
    folder_id = extract_folder_id(url_or_id)
    if not folder_id:
        return None
    
    cfg = load_config()
    # Check if folder already exists
    for f in cfg["folders"]:
        if f.get("id") == folder_id:
            f["name"] = name
            f["default_dest"] = os.path.abspath(default_dest)
            f["url"] = url_or_id
            save_config(cfg)
            return f
            
    folder_entry = {
        "id": folder_id,
        "name": name,
        "url": url_or_id,
        "default_dest": os.path.abspath(default_dest)
    }
    cfg["folders"].append(folder_entry)
    save_config(cfg)
    return folder_entry

def update_folder(
    folder_id: str,
    new_name: Optional[str] = None,
    new_url_or_id: Optional[str] = None,
    new_dest: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Updates an existing monitored drive's alias, link, or destination path."""
    cfg = load_config()
    target_folder = None
    for f in cfg["folders"]:
        if f.get("id") == folder_id:
            target_folder = f
            break

    if not target_folder:
        return None

    if new_name is not None and new_name.strip():
        target_folder["name"] = new_name.strip()

    if new_dest is not None and new_dest.strip():
        target_folder["default_dest"] = os.path.abspath(new_dest.strip())

    if new_url_or_id is not None and new_url_or_id.strip():
        new_fid = extract_folder_id(new_url_or_id)
        if new_fid:
            target_folder["id"] = new_fid
            target_folder["url"] = new_url_or_id.strip()

    save_config(cfg)
    return target_folder

def remove_folder(folder_id: str) -> bool:
    cfg = load_config()
    original_len = len(cfg["folders"])
    cfg["folders"] = [f for f in cfg["folders"] if f.get("id") != folder_id]
    if len(cfg["folders"]) < original_len:
        save_config(cfg)
        return True
    return False
