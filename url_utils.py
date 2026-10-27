import re
from typing import Optional

def extract_folder_id(url_or_id: str) -> Optional[str]:
    """
    Extracts the Google Drive folder ID from a URL or raw ID string.
    Supports:
      - https://drive.google.com/drive/folders/{id}
      - https://drive.google.com/drive/u/{n}/folders/{id}
      - https://drive.google.com/open?id={id}
      - Raw ID strings
    """
    if not url_or_id:
        return None
    
    url_or_id = url_or_id.strip()
    
    # Check for /folders/<id> pattern
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1)
    
    # Check for id=<id> parameter
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1)
    
    # If string is alphanumeric with typical Drive ID length and no slashes
    if re.fullmatch(r'[a-zA-Z0-9_-]{15,60}', url_or_id):
        return url_or_id
        
    return None
