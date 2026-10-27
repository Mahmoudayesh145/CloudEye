from typing import List, Dict, Any, Tuple, Optional, Set
from cache_manager import is_new_or_modified

def format_size(bytes_size: int) -> str:
    """Formats bytes into human readable format (KB, MB, GB)."""
    if not bytes_size or bytes_size <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def _scan_folder_recursive(
    drive_service,
    current_folder_id: str,
    root_folder_id: str,
    root_folder_name: str,
    current_rel_path: str,
    default_dest: str,
    visited_folders: Set[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """
    Recursively scans Google Drive folder and all its nested subfolders.
    Returns: (new_or_modified_files, all_files, error_list)
    """
    new_files = []
    all_files = []
    errors = []

    if current_folder_id in visited_folders:
        return new_files, all_files, errors
    visited_folders.add(current_folder_id)

    page_token = None
    subfolders_to_visit = []

    try:
        while True:
            response = drive_service.files().list(
                q=f"'{current_folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                pageSize=100,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            items = response.get('files', [])
            for item in items:
                is_folder = item.get('mimeType') == 'application/vnd.google-apps.folder'
                item_name = item.get("name", "Unnamed")

                if is_folder:
                    # Queue subfolder for recursive inspection
                    new_rel = f"{current_rel_path}/{item_name}" if current_rel_path else item_name
                    subfolders_to_visit.append((item.get("id"), new_rel))
                else:
                    item_info = {
                        "id": item.get("id"),
                        "name": item_name,
                        "mimeType": item.get("mimeType"),
                        "size": int(item.get("size", 0) or 0),
                        "size_formatted": format_size(int(item.get("size", 0) or 0)),
                        "createdTime": item.get("createdTime"),
                        "modifiedTime": item.get("modifiedTime"),
                        "webViewLink": item.get("webViewLink", ""),
                        "folder_id": root_folder_id,
                        "folder_name": root_folder_name,
                        "subfolder_path": current_rel_path,
                        "display_path": f"{root_folder_name}/{current_rel_path}/{item_name}" if current_rel_path else f"{root_folder_name}/{item_name}",
                        "default_dest": default_dest,
                        "is_folder": False
                    }
                    all_files.append(item_info)
                    if is_new_or_modified(item_info):
                        new_files.append(item_info)

            page_token = response.get('nextPageToken', None)
            if not page_token:
                break

    except Exception as e:
        errors.append(f"Folder '{current_rel_path or root_folder_name}': {str(e)}")

    # Recurse into all nested subfolders
    for sub_id, sub_rel in subfolders_to_visit:
        sub_new, sub_all, sub_errs = _scan_folder_recursive(
            drive_service=drive_service,
            current_folder_id=sub_id,
            root_folder_id=root_folder_id,
            root_folder_name=root_folder_name,
            current_rel_path=sub_rel,
            default_dest=default_dest,
            visited_folders=visited_folders
        )
        new_files.extend(sub_new)
        all_files.extend(sub_all)
        errors.extend(sub_errs)

    return new_files, all_files, errors

def scan_folder(
    drive_service,
    folder_id: str,
    folder_name: str,
    default_dest: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """
    Entry point to scan a root folder and all its subdirectories recursively.
    """
    visited = set()
    new_files, all_files, errors = _scan_folder_recursive(
        drive_service=drive_service,
        current_folder_id=folder_id,
        root_folder_id=folder_id,
        root_folder_name=folder_name,
        current_rel_path="",
        default_dest=default_dest,
        visited_folders=visited
    )
    err_str = "; ".join(errors) if errors else None
    return new_files, all_files, err_str

def scan_all_folders(
    drive_service,
    folders_config: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, str]]:
    """
    Scans all configured folders recursively and returns:
    (all_new_files, all_total_files, errors_by_folder)
    """
    all_new_files = []
    all_total_files = []
    errors = {}

    for folder in folders_config:
        fid = folder.get("id")
        fname = folder.get("name", "Unnamed Folder")
        fdest = folder.get("default_dest", "")

        new_files, all_files, err = scan_folder(drive_service, fid, fname, fdest)
        if err:
            errors[fname] = err
        all_new_files.extend(new_files)
        all_total_files.extend(all_files)

    return all_new_files, all_total_files, errors
