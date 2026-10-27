import os
import sys
import subprocess
from typing import Tuple, Dict, Any

TASK_NAME = "CloudEye_AutoMonitor"

def get_pythonw_path() -> str:
    """Returns path to pythonw.exe for silent, windowless background execution."""
    py_dir = os.path.dirname(sys.executable)
    pyw = os.path.join(py_dir, "pythonw.exe")
    if os.path.exists(pyw):
        return pyw
    return sys.executable

def is_task_scheduled() -> bool:
    """Checks if the Windows scheduled task exists and is active."""
    try:
        cmd = ["schtasks", "/Query", "/TN", TASK_NAME]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def get_task_info() -> Dict[str, Any]:
    """Gets details about the scheduled task."""
    try:
        cmd = ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return {"configured": False, "status": "Inactive"}

        info = {"configured": True, "status": "Active"}
        for line in res.stdout.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                k = key.strip().lower()
                v = val.strip()
                if "status" in k:
                    info["state"] = v
                elif "next run time" in k:
                    info["next_run"] = v
        return info
    except Exception as e:
        return {"configured": False, "status": "Error", "error": str(e)}

def register_background_task(interval_minutes: int = 60) -> Tuple[bool, str]:
    """
    Registers a background Windows Scheduled Task to run CloudEye silently.
    Uses pythonw.exe so no black console window ever appears.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pyw = get_pythonw_path()
        main_py = os.path.join(base_dir, "main.py")
        task_cmd = f'"{pyw}" "{main_py}" --check'

        if interval_minutes >= 60 and interval_minutes % 60 == 0:
            sc_type = "HOURLY"
            sc_mo = str(interval_minutes // 60)
        else:
            sc_type = "MINUTE"
            sc_mo = str(interval_minutes)

        cmd = [
            "schtasks", "/Create",
            "/TN", TASK_NAME,
            "/TR", task_cmd,
            "/SC", sc_type,
            "/MO", sc_mo,
            "/F"
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return True, f"Background task registered: CloudEye will silently scan every {interval_minutes} minutes."
        else:
            return False, res.stderr or res.stdout or "Failed to register task."
    except Exception as e:
        return False, str(e)

def remove_background_task() -> Tuple[bool, str]:
    """Removes the background Windows Scheduled Task."""
    try:
        cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 or "cannot find" in (res.stderr or "").lower():
            return True, "Background automated task removed successfully."
        else:
            return False, res.stderr or res.stdout or "Failed to remove task."
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    ok, msg = register_background_task(60)
    print("Registered:", ok, msg)
    print("Info:", get_task_info())
