import os
import sys
import subprocess
import ctypes

def refresh_windows_icon_cache():
    """Forces Windows Explorer to refresh its icon cache immediately."""
    try:
        # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
    except Exception:
        pass

def create_desktop_shortcut():
    """
    Creates or updates the 'CloudEye.lnk' shortcut on the user's Desktop with the custom logo.ico icon.
    Points TargetPath directly to python.exe so Windows Explorer displays the custom icon reliably.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        py_exe = sys.executable
        main_py = os.path.join(base_dir, "main.py")
        ico_path = os.path.join(base_dir, "cloudeye.ico")

        ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$desk = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desk "CloudEye.lnk"

# Remove existing shortcut if present so Windows reloads icon from scratch
if (Test-Path $shortcutPath) {{
    Remove-Item -Path $shortcutPath -Force
}}

$s = $ws.CreateShortcut($shortcutPath)
$s.TargetPath = "{py_exe}"
$s.Arguments = '"{main_py}"'
$s.WorkingDirectory = "{base_dir}"
$s.IconLocation = "{ico_path},0"
$s.Description = "CloudEye - Google Drive Monitor & Sync Engine"
$s.Save()

Write-Output "SUCCESS: Created at $shortcutPath"
"""
        ps_file = os.path.join(base_dir, "_temp_shortcut.ps1")
        with open(ps_file, "w", encoding="utf-8") as f:
            f.write(ps_script)

        res = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True
        )

        if os.path.exists(ps_file):
            os.remove(ps_file)

        # Notify Windows Explorer of icon change
        refresh_windows_icon_cache()

        return "SUCCESS" in res.stdout
    except Exception as e:
        print(f"Notice: Could not update desktop shortcut: {e}")
        return False

if __name__ == "__main__":
    result = create_desktop_shortcut()
    print("Desktop shortcut updated with new logo:", result)
