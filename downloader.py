import io
import os
from typing import Optional, Tuple
from googleapiclient.http import MediaIoBaseDownload
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn
)
from cache_manager import mark_file_downloaded

def download_file(
    drive_service,
    file_id: str,
    file_name: str,
    target_dir: str,
    subfolder_path: str = "",
    total_size: int = 0
) -> Tuple[bool, Optional[str], str]:
    """
    Downloads a single file from Google Drive to target_dir, preserving subfolder structure.
    Returns (success, error_message, final_destination_path).
    """
    try:
        # Reconstruct subfolder tree if present
        if subfolder_path:
            clean_sub = subfolder_path.replace("/", os.sep).replace("\\", os.sep).strip(os.sep)
            final_target_dir = os.path.join(target_dir, clean_sub)
        else:
            final_target_dir = target_dir

        os.makedirs(final_target_dir, exist_ok=True)
        dest_path = os.path.join(final_target_dir, file_name)

        # Handle filename collisions by appending (1), (2), etc.
        base_name, ext = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(final_target_dir, f"{base_name} ({counter}){ext}")
            counter += 1

        request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[filename]}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task(
                "download",
                filename=os.path.basename(dest_path),
                total=total_size if total_size > 0 else None
            )

            with open(dest_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request, chunksize=1024 * 1024 * 4) # 4MB chunks
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress.update(
                            task_id,
                            completed=status.resumable_progress,
                            total=status.total_size if status.total_size else total_size
                        )

        mark_file_downloaded(file_id, dest_path)
        return True, None, dest_path

    except Exception as e:
        # If download failed and partially written, clean up
        if 'dest_path' in locals() and os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception:
                pass
        return False, str(e), ""
