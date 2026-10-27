# CloudEye

Autonomous Google Drive Monitor, Deep Structure Sync Engine, and Notification Daemon.

Repository: [Mahmoudayesh145/CloudEye](https://github.com/Mahmoudayesh145/CloudEye)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Repository Structure and File Classification](#repository-structure-and-file-classification)
  - [Public Files (To Commit and Upload)](#public-files-to-commit-and-upload)
  - [Private Files (Never Commit - Excluded by .gitignore)](#private-files-never-commit---excluded-by-gitignore)
- [Prerequisites](#prerequisites)
- [Step-by-Step Guide: Generating Private Google Cloud Credentials](#step-by-step-guide-generating-private-google-cloud-credentials)
  - [Step 1: Create a Google Cloud Project](#step-1-create-a-google-cloud-project)
  - [Step 2: Enable Google Drive API and Gmail API](#step-2-enable-google-drive-api-and-gmail-api)
  - [Step 3: Configure the OAuth Consent Screen](#step-3-configure-the-oauth-consent-screen)
  - [Step 4: Add Authorized Test Users](#step-4-add-authorized-test-users)
  - [Step 5: Create Desktop OAuth Client Credentials](#step-5-create-desktop-oauth-client-credentials)
  - [Step 6: Place and Name credentials.json](#step-6-place-and-name-credentialsjson)
  - [Step 7: Configure Local Settings (config.json)](#step-7-configure-local-settings-configjson)
- [Installation and Quick Start](#installation-and-quick-start)
- [Terminal Menu Reference](#terminal-menu-reference)
- [All Data Inventory Mode](#all-data-inventory-mode)
- [Silent Background Automation (Windows Task Scheduler)](#silent-background-automation-windows-task-scheduler)
- [Security, Privacy, and Data Governance](#security-privacy-and-data-governance)
- [Troubleshooting and Common Questions](#troubleshooting-and-common-questions)
- [License and Attribution](#license-and-attribution)

---

## Overview

CloudEye is a Python-based console application and background daemon engineered to monitor multiple Google Drive folders recursively, detect newly published or updated files across all nested subdirectories, dispatch structured Gmail alert digests, and provide an interactive terminal interface for selective downloading while preserving complete directory hierarchies locally.

Designed for researchers, engineers, students, and teams managing distributed cloud drives, CloudEye eliminates manual folder checking and redundant downloads through local SQLite state caching and native Windows Task Scheduler integration.

---

## Key Features

- Deep Recursive Subfolder Tracking: Scans root Drive folders along with every nested child folder, regardless of directory tree depth.
- Multi-Drive Alias Isolation: Categorizes and displays detected files cleanly separated by user-defined Drive aliases (e.g., "Work Assets", "University Lectures").
- All Data Inventory: Provides a complete chronological directory listing of all files across all monitored drives sorted by creation or modification timestamp, allowing downloading of any file at any point in time.
- Automated Gmail Alert Digests: Automatically compiles and delivers formatted HTML and plain-text summaries of newly detected files directly to your designated email inbox.
- Local Directory Tree Preservation: Automatically recreates the exact remote nested folder hierarchy when downloading files to your designated local storage target.
- Interactive Multi-Select Terminal: Fast keyboard navigation (`SPACE` to select/unselect, `ENTER` to confirm) powered by `questionary` and `rich`.
- Silent Background Monitoring: Integrates with Windows Task Scheduler using `pythonw.exe` to execute periodic headless scans (`--check`) without popping up console windows or interrupting your active workflow.
- Drive and Path Management: Update aliases, remote Drive links, and local destination paths dynamically without modifying code or raw JSON files.
- Local Activity and Cache Tracking: Employs an embedded SQLite database (`monitor_cache.db`) for tracking seen items, MD5 checksums, modification dates, and download history.
- Desktop Integration: Generates a custom Windows Desktop shortcut (`CloudEye.lnk`) mapped to a transparent multi-resolution icon (`cloudeye.ico`).

---

## System Architecture

```text
+-------------------------------------------------------------------------------+
|                                    CloudEye                                   |
+-------------------------------------------------------------------------------+
       |                                                    |
       v [Interactive Terminal]                             v [Headless Daemon: --check]
+------------------------------------+             +----------------------------------+
|           main.py (CLI)            |             | Windows Task Scheduler (pythonw) |
+------------------------------------+             +----------------------------------+
       |                                                    |
       +-------------------------+--------------------------+
                                 |
                                 v
                     +-----------------------+
                     |    auth.py (OAuth)    | <--- credentials.json / token.json
                     +-----------------------+
                                 |
        +------------------------+------------------------+
        |                                                 |
        v                                                 v
+-------------------------------+             +------------------------------+
| drive_scanner.py (Drive v3)   |             | email_notifier.py (Gmail v1) |
| - Recursive tree traversal    |             | - Multipart HTML digests     |
| - Pagination & folder mapping |             | - Direct API delivery        |
+-------------------------------+             +------------------------------+
        |                                                 |
        v                                                 |
+-------------------------------+                         |
| cache_manager.py (SQLite)     |                         |
| - monitor_cache.db            |                         |
| - State & checksum tracking   |                         |
+-------------------------------+                         |
        |                                                 |
        v                                                 |
+-------------------------------+                         |
| downloader.py (MediaIoBase)   |                         |
| - Chunked stream downloads    |                         |
| - Local folder tree builder   |                         |
+-------------------------------+                         |
        |                                                 |
        +------------------------+------------------------+
                                 |
                                 v
                        [Local File System]
```

---

## Repository Structure and File Classification

When preparing this project for upload to GitHub (`Mahmoudayesh145/CloudEye`), it is critical to distinguish between public source code and private, sensitive data.

### Public Files (To Commit and Upload)

These files contain the application logic, templates, assets, and documentation. They are safe to push to a public or private GitHub repository:

| File Name | Description |
| :--- | :--- |
| `main.py` | Primary interactive CLI interface, banner renderer, and background argument dispatcher (`--check`). |
| `auth.py` | Google OAuth 2.0 flow handler with automatic token generation and refresh capabilities. |
| `drive_scanner.py` | Recursive Drive API v3 directory scanner supporting nested trees and pagination. |
| `downloader.py` | Chunked file downloader supporting streaming transfers and local directory structure recreation. |
| `email_notifier.py` | Gmail API v1 notification service formatting HTML and plain-text change digests. |
| `cache_manager.py` | SQLite state manager handling file tracking, seen state, and download logs. |
| `config_manager.py` | Configuration abstraction layer for reading and updating `config.json`. |
| `scheduler_manager.py` | Windows Task Scheduler manager creating and removing silent background tasks. |
| `shortcut_utils.py` | Windows Shell shortcut generator for desktop access with custom icon bindings. |
| `url_utils.py` | Robust URL and folder ID parser extracting Drive IDs from varied link formats. |
| `config.example.json` | Anonymized configuration template showing the required schema. |
| `requirements.txt` | Complete list of pinned Python dependencies. |
| `run.bat` | Windows batch launcher enforcing UTF-8 code page (`chcp 65001`). |
| `cloudeye.ico` | High-resolution multi-layer icon file (16px to 256px) for Windows shortcuts. |
| `logo.png` | Transparent logo asset used for documentation and interfaces. |
| `.gitignore` | Git exclusion rules protecting private credentials, databases, and temporary files. |
| `README.md` | Comprehensive architectural and operational documentation. |

### Private Files (Never Commit - Excluded by .gitignore)

The following files contain personal identity tokens, cloud secret keys, specific monitored drive targets, and local machine databases. They are strictly excluded by `.gitignore` and must NEVER be uploaded:

| File Name | Reason for Exclusion | How It Is Created |
| :--- | :--- | :--- |
| `credentials.json` | Contains Google Cloud OAuth 2.0 client ID and client secret. | Downloaded manually from Google Cloud Console. |
| `client_secret_*.json` | Default name pattern for downloaded Google OAuth client secrets. | Downloaded manually from Google Cloud Console. |
| `token.json` | Contains authorized user access token and refresh token for Drive and Gmail scopes. | Generated automatically on first login. |
| `config.json` | Contains user profile name, destination email address, and drive links/paths. | Created locally by copying `config.example.json` or on first run. |
| `monitor_cache.db` | Local SQLite database recording file IDs, names, checksums, and download timestamps. | Generated automatically by `cache_manager.py`. |
| `__pycache__/` | Compiled Python bytecode files. | Generated automatically by the Python runtime. |

---

## Prerequisites

- Operating System: Windows 10, Windows 11, or Windows Server (Native integration with Windows Task Scheduler).
- Python: Version 3.10, 3.11, or 3.12 (with `pip` package manager installed and added to `PATH`).
- Google Account: A standard Gmail or Google Workspace account with access to the monitored Drive folders.

---

## Step-by-Step Guide: Generating Private Google Cloud Credentials

To connect CloudEye to Google Drive and Gmail without hardcoded secrets, each user must create their own OAuth 2.0 Client credentials via the Google Cloud Console. Follow these instructions:

### Step 1: Create a Google Cloud Project

1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Log in using the Google account you intend to use for Drive access and Gmail notifications.
3. In the top navigation bar, click the project dropdown menu and click **New Project**.
4. Set **Project Name** to `CloudEye-Monitor` (or your preferred name).
5. Leave Organization set to `No organization` (unless using Google Workspace) and click **Create**.
6. Ensure your new project is selected in the top navigation bar before proceeding.

### Step 2: Enable Google Drive API and Gmail API

1. In the left navigation menu, open **APIs & Services** > **Library**.
2. In the search bar, type `Google Drive API` and hit Enter.
3. Click on **Google Drive API** from the results and click the blue **Enable** button.
4. Return to **APIs & Services** > **Library**.
5. In the search bar, type `Gmail API` and hit Enter.
6. Click on **Gmail API** from the results and click the blue **Enable** button.

### Step 3: Configure the OAuth Consent Screen

1. Open **APIs & Services** > **OAuth consent screen** from the left sidebar.
2. Select **External** as the User Type and click **Create**.
3. Under **App information**:
   - **App name**: `CloudEye`
   - **User support email**: Select your own Gmail address.
4. Under **Developer contact information**:
   - **Email addresses**: Enter your own Gmail address.
5. Click **Save and Continue**.
6. On the **Scopes** page:
   - Click **Add or Remove Scopes**.
   - Search for and select:
     - `.../auth/drive.readonly` (See and download all your Google Drive files)
     - `.../auth/gmail.send` (Send email on your behalf)
   - Click **Update**, then click **Save and Continue**.

### Step 4: Add Authorized Test Users

While the OAuth consent screen is in "Testing" mode (which is free and requires no Google verification), you must explicitly authorize your email:

1. On the **Test users** step of the OAuth consent screen setup, click **Add Users**.
2. Enter your primary Gmail address (the exact account that owns or accesses the monitored drives and will receive notifications).
3. Click **Add**, then verify your email appears in the Test Users list.
4. Click **Save and Continue**, then click **Back to Dashboard**.

### Step 5: Create Desktop OAuth Client Credentials

1. In the left sidebar, navigate to **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** at the top of the page and select **OAuth client ID**.
3. Under **Application type**, select **Desktop app**.
4. Under **Name**, enter `CloudEye Desktop Client`.
5. Click **Create**.
6. A dialog titled "OAuth client created" will appear. Click **Download JSON**.

### Step 6: Place and Name credentials.json

1. Locate the downloaded file on your computer (typically named `client_secret_<long_id>.apps.googleusercontent.com.json` in your Downloads folder).
2. Move this file directly into the root folder of CloudEye (e.g., `f:\M\Monitor\`).
3. Rename the file to:
   ```text
   credentials.json
   ```
   *(Note: CloudEye also supports files named `client_secret_*.json` automatically, but renaming to `credentials.json` is recommended).*

### Step 7: Configure Local Settings (config.json)

1. In the project directory, copy `config.example.json` and name the copy `config.json`:
   ```bash
   cp config.example.json config.json
   ```
2. Open `config.json` in any text editor. Its structure should be:
   ```json
   {
       "username": "Your Name",
       "notification_email": "your_email@gmail.com",
       "folders": [
           {
               "alias": "Main Project",
               "folder_id": "1abcXYZ_ExampleGoogleDriveFolderID",
               "local_path": "C:\\CloudEye_Downloads\\Main Project"
           }
       ]
   }
   ```
3. Alternatively, simply leave `config.json` empty or run `main.py`; the onboarding wizard will guide you through setting your name, notification email, and first drive folder interactively!

---

## Installation and Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Mahmoudayesh145/CloudEye.git
cd CloudEye
```

### 2. Set Up a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

Install the required libraries listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

The core dependencies include:
- `google-api-python-client`: Official Google client library for Drive and Gmail API communication.
- `google-auth-oauthlib`: User authorization flow and token acquisition.
- `google-auth-httplib2`: HTTP transport layer for Google authentication.
- `rich`: Formatting, dynamic tables, status indicators, and progress bars.
- `questionary`: Prompt-driven interactive terminal navigation.

### 4. Run CloudEye

To start CloudEye, run:

```bash
python main.py
```

Or double-click `run.bat` in Windows Explorer.

On first launch:
- If `credentials.json` is present, CloudEye will open your default browser to authorize access.
- Review and approve the requested read-only Drive permissions and Gmail send permissions.
- If Google displays an "App isn't verified" notice, click **Advanced** > **Go to CloudEye (unsafe)**. (This warning is standard for private developer projects in Testing mode).
- Once approved, `token.json` is generated locally, and you will not need to authenticate via browser again.
- A desktop shortcut named **CloudEye** will be created on your Windows Desktop for one-click access.

---

## Terminal Menu Reference

When launched in interactive mode, CloudEye presents an organized control panel:

```text
[+]  Add new drive to monitor
[*]  View updates & download
[D]  All Data (Browse & download any file)
[#]  Manage saved drives (paths & links)
[A]  Auto-monitor in background [ON/OFF]
[i]  History of downloading
[u]  Update username
[@]  Change notification email
[x]  Exit CloudEye
```

### Detailed Breakdown of Options

- `[+] Add new drive to monitor`:
  Prompts first for an intuitive Alias Name (e.g., "Math Lectures"), then accepts a Google Drive URL or Folder ID, and finally prompts for your chosen local destination path.

- `[*] View updates & download`:
  Connects to Google Drive, scans all monitored drives recursively, identifies new or modified files not previously seen in `monitor_cache.db`, and groups the files into clean tables separated by Drive Alias. Dispatches a Gmail alert digest and offers an interactive checklist (`SPACE` to select, `ENTER` to download).

- `[D] All Data (Browse & download any file)`:
  Displays the full catalog of all files across all monitored drives, grouped by Drive Alias and sorted chronologically (newest published/modified first). Enables searching, browsing, and on-demand downloading of any file at any time.

- `[#] Manage saved drives (paths & links)`:
  Displays a formatted overview of all monitored drives. Allows selecting any drive to update its Alias Name, change its Google Drive Link / Folder ID, modify its Local Download Path, or remove it from tracking.

- `[A] Auto-monitor in background [ON/OFF]`:
  Enables or disables the silent Windows Task Scheduler background worker (`CloudEye_AutoMonitor`). Allows choosing the automated scan frequency (every 30 minutes, 1 hour, 2 hours, or 4 hours).

- `[i] History of downloading`:
  Displays a log of previously downloaded files, local storage locations, file sizes, and timestamps. Includes an option to safely clear history or reset the cache.

- `[u] Update username`:
  Modifies the personalized greeting name stored in `config.json`.

- `[@] Change notification email`:
  Updates the recipient Gmail address where alert digests are sent.

- `[x] Exit CloudEye`:
  Safely closes database connections and exits the application.

---

## All Data Inventory Mode

A frequent problem with notification systems is that once an update has been viewed or cleared, older files become difficult to locate and re-download.

CloudEye addresses this with the `[D] All Data` mode:
1. Performs a live recursive traversal across all configured drives.
2. Organizes every discovered file under its corresponding Drive Alias.
3. Sorts all entries chronologically by modification / publish timestamp with the newest items on top.
4. Identifies files that have already been retrieved locally (`[Downloaded]`) versus files available on Drive (`[Available]`).
5. Allows users to select any combination of files using `[SPACE]` and download them immediately to their configured local folder.

---

## Silent Background Automation (Windows Task Scheduler)

CloudEye includes a native background scheduler designed specifically for Windows environments.

### How It Operates

- Command Line Execution: The scheduler runs:
  ```text
  pythonw.exe "f:\M\Monitor\main.py" --check
  ```
- No Console Windows: By using `pythonw.exe` rather than `python.exe`, Windows runs the script completely headlessly in the background. No command prompt windows will appear or steal keyboard focus.
- Efficient Checking: When invoked with the `--check` argument, CloudEye:
  1. Reads `config.json` for saved drives and recipient email.
  2. Traverses all monitored folders and subfolders.
  3. Queries `monitor_cache.db` to isolate new or modified files.
  4. If changes are detected, compiles and delivers a Gmail alert digest and updates `monitor_cache.db`.
  5. If no changes are detected, silently exits in seconds.
- Native Task: The task is registered directly in Windows Task Scheduler under the identifier `CloudEye_AutoMonitor`.

### Manual Inspection

You can view or inspect the scheduled task in Windows PowerShell:

```powershell
schtasks /Query /TN "CloudEye_AutoMonitor" /FO LIST /V
```

To delete the task manually from command line:

```powershell
schtasks /Delete /TN "CloudEye_AutoMonitor" /F
```

---

## Security, Privacy, and Data Governance

CloudEye is designed with strict data privacy principles:

1. Zero Third-Party Telemetry: CloudEye does not communicate with any external servers, analytic endpoints, or databases. The only network connections made are directly to official Google APIs (`googleapis.com`).
2. Local Credential Storage: All authorization tokens (`token.json`), client secrets (`credentials.json`), user preferences (`config.json`), and index states (`monitor_cache.db`) reside exclusively on your local machine.
3. Minimal Permission Scopes:
   - Drive Scope: `https://www.googleapis.com/auth/drive.readonly` (Strictly read-only; CloudEye has zero permission to delete, modify, or overwrite your cloud files).
   - Gmail Scope: `https://www.googleapis.com/auth/gmail.send` (Strictly send; CloudEye cannot read your incoming mail, search messages, or access your inbox).
4. Safe Version Control Practices: The included `.gitignore` guarantees that your private tokens and database files will never be staged or committed to GitHub repositories.

---

## Troubleshooting and Common Questions

### Issue: Error 403 "Access Blocked: Drive Monitor has not completed the Google verification process"

- Cause: The Google Cloud project OAuth Consent Screen is in "Testing" mode and your personal email has not been added to the authorized Test Users list.
- Solution:
  1. Open [Google Cloud Console](https://console.cloud.google.com/).
  2. Navigate to **APIs & Services** > **OAuth consent screen**.
  3. Scroll to **Test users** and click **Add Users**.
  4. Add the exact Gmail address you are logging in with and click **Save**.
  5. Delete `token.json` locally and run `python main.py` again.

### Issue: UnicodeEncodeError or Garbled Characters in Command Prompt

- Cause: Windows Command Prompt defaults to regional code pages (such as `cp1256` or `cp1252`) which cannot represent standard box-drawing characters.
- Solution: Run CloudEye via `run.bat` or manually set your console code page to UTF-8 before launching:
  ```cmd
  chcp 65001
  python main.py
  ```

### Issue: Desktop Shortcut Icon Appears as Generic Batch File

- Cause: Windows caches icons aggressively and standard shortcut targets to `.bat` files often suppress custom `.ico` assignments.
- Solution: CloudEye automatically creates shortcuts pointing directly to `python.exe` with arguments targeting `main.py` and binds `cloudeye.ico` using native Windows shell calls (`SHChangeNotify`). If your icon does not update, right-click the shortcut, select **Properties** > **Change Icon**, and browse to `cloudeye.ico`.

---

## License and Attribution

Developed and maintained by [Mahmoud Ahmed Ayesh](https://github.com/Mahmoudayesh145).

Source repository: [https://github.com/Mahmoudayesh145/CloudEye](https://github.com/Mahmoudayesh145/CloudEye)

Distributed under the MIT License. You are free to modify, distribute, and integrate this software in private and commercial projects according to the terms of the license.
