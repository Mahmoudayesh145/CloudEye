import os
import sys

# Configure UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        os.system("chcp 65001 > nul 2>&1")
        # Ensure Taskbar displays custom icon rather than generic Python icon
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('cloudeye.drivemonitor.engine.v2')
    except Exception:
        pass

import argparse
from datetime import datetime
from typing import List, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
import questionary

import auth
import config_manager
import cache_manager
import drive_scanner
import email_notifier
import downloader
import shortcut_utils
import scheduler_manager
from url_utils import extract_folder_id

console = Console(force_terminal=True)

# Custom Questionary Style: clean text CLI style without relying on graphical icons
custom_style = questionary.Style([
    ('qmark', 'fg:#00d2ff bold'),       # token in front of the question
    ('question', 'bold'),               # question text
    ('answer', 'fg:#00ff88 bold'),      # submitted answer text
    ('pointer', 'fg:#00d2ff bold'),     # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#00d2ff bold'), # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#00ff88'),         # checked item in checkbox
    ('separator', 'fg:#666666'),        # separator in lists
    ('instruction', 'fg:#888888'),      # user instructions
    ('text', ''),                       # plain text
])

def get_time_based_greeting(username: str) -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        period = "Good morning"
    elif 12 <= hour < 17:
        period = "Good afternoon"
    elif 17 <= hour < 22:
        period = "Good evening"
    else:
        period = "Good night"

    if username:
        return f"[bold cyan]>> {period}, [bold bright_white]{username}[/bold bright_white]![/bold cyan]"
    return f"[bold cyan]>> {period}![/bold cyan]"

def display_banner(username: str = ""):
    console.clear()
    
    # Styled CloudEye ANSI Block Art
    logo_art = """[bold #0088ff]               ▄▄██████████▄▄
            ▄██████████████████▄
         ▄██████▀▀        ▀▀██████▄
 ▄▄██████████▀     [bold white on #051030]▄██████▄[/]     ▀███████▄
████████████     [bold white on #051030]███▀  ▀███[/]     ████████
████   ██████     [bold white on #051030]███ ▄▄ ███[/]     ████████
████   ██████     [bold white on #051030]██████████[/]     ████████
 ████████████     [bold white on #051030]▀████████▀[/]     ████████
  ▀▀██████████▄              ▄███████▀
         ▀██████▄▄        ▄▄██████▀
            ▀▀████████████████▀▀[/]"""

    console.print(Align.center(logo_art))
    
    title_text = Text("C L O U D E Y E", justify="center", style="bold bright_cyan")
    subtitle_text = Text(
        "Autonomous Google Drive Monitor & Deep Structure Sync Engine\n"
        "Recursive Subfolder Tracking • Instant Gmail Digests • Precision Downloader",
        justify="center",
        style="dim white"
    )

    console.print(Align.center(title_text))
    console.print(Align.center(subtitle_text))
    console.print("")

    if username:
        greeting = get_time_based_greeting(username)
        console.print(Align.center(greeting))
        console.print("")

def check_credentials_or_guide() -> bool:
    if not auth.check_credentials_exist():
        console.print(Panel(
            "[bold red]Google Cloud Credentials Missing![/bold red]\n\n"
            "To use CloudEye with your Google Drive and Gmail:\n"
            "1. Download your OAuth client JSON file from Google Cloud Console.\n"
            "2. Rename it to [bold yellow]credentials.json[/bold yellow] and place it in:\n"
            f"   [bold green]{os.path.dirname(os.path.abspath(__file__))}[/bold green]\n\n"
            "Once placed, re-run CloudEye!",
            title="Setup Required",
            border_style="yellow"
        ))
        return False
    return True

def ensure_user_onboarding() -> str:
    """Prompts for user name and notification email on first run."""
    username = config_manager.get_username()
    email = config_manager.get_notification_email()

    needs_setup = not username or not email
    if needs_setup:
        display_banner()
        console.print("[bold bright_cyan]─── Welcome to CloudEye Setup! ───[/bold bright_cyan]")
        console.print("[white]Let's configure your profile and alert preferences (one-time setup).[/white]\n")

        if not username:
            name = questionary.text(
                "What should CloudEye call you? (Enter your name):",
                style=custom_style
            ).ask()
            if name and name.strip():
                username = name.strip()
                config_manager.set_username(username)

        if not email:
            notif_email = questionary.text(
                "Enter your Gmail address to receive update alert digests:",
                style=custom_style
            ).ask()
            if notif_email and notif_email.strip():
                email = notif_email.strip()
                config_manager.set_notification_email(email)

        # Create desktop shortcut automatically on first onboarding
        shortcut_utils.create_desktop_shortcut()
        console.print("\n[bold green][OK] Initial setup completed successfully![/bold green]\n")
        questionary.press_any_key_to_continue("Press any key to enter CloudEye...").ask()

    return username

def handle_add_drive():
    console.print("\n[bold bright_cyan]─── Add New Google Drive to Monitor ───[/bold bright_cyan]")
    console.print("[dim]CloudEye will monitor ALL files and nested subfolder structures recursively.[/dim]\n")

    # Step 1: Ask for Alias Name first
    alias_name = questionary.text(
        "Enter an alias / friendly name for this drive (e.g. 'Project Files' or 'Work Assets'):",
        style=custom_style
    ).ask()

    if not alias_name or not alias_name.strip():
        console.print("[yellow]Operation cancelled: Alias cannot be empty.[/yellow]\n")
        questionary.press_any_key_to_continue().ask()
        return

    alias = alias_name.strip()

    # Step 2: Ask for Google Drive link or ID
    url_or_id = questionary.text(
        f"Enter Google Drive Folder Link or Folder ID for '{alias}':",
        style=custom_style
    ).ask()

    if not url_or_id or not url_or_id.strip():
        console.print("[yellow]Operation cancelled.[/yellow]\n")
        return

    folder_id = extract_folder_id(url_or_id)
    if not folder_id:
        console.print("[bold red]Invalid Google Drive link or ID! Please ensure it is a valid folder link.[/bold red]\n")
        questionary.press_any_key_to_continue().ask()
        return

    # Step 3: Ask for Download destination location
    default_suggested_dest = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Downloads",
        alias.replace(" ", "_")
    )

    default_dest = questionary.text(
        f"Choose local download directory for '{alias}':",
        default=default_suggested_dest,
        style=custom_style
    ).ask()

    if not default_dest or not default_dest.strip():
        default_dest = default_suggested_dest
    else:
        default_dest = default_dest.strip()

    result = config_manager.add_folder(alias, url_or_id.strip(), default_dest)
    if result:
        console.print(f"\n[bold green][OK] Added '{alias}' successfully![/bold green]")
        console.print(f"[dim]Folder ID: {folder_id}[/dim]")
        console.print(f"[dim]Download Location: {default_dest}[/dim]\n")
    else:
        console.print("[bold red]Failed to save folder to configuration.[/bold red]\n")

    questionary.press_any_key_to_continue("Press any key to return to menu...").ask()

def handle_view_updates(auto_mode: bool = False):
    """Checks all saved monitoring links, detects updates in nested structures, sends email, and downloads."""
    console.print("\n[bold bright_cyan]─── Checking for Updates in Monitored Drives ───[/bold bright_cyan]\n")

    if not check_credentials_or_guide():
        return

    folders = config_manager.get_folders()
    if not folders:
        console.print("[yellow]No Google Drive folders are currently monitored.[/yellow]")
        if questionary.confirm("Would you like to add a drive to monitor now?", style=custom_style).ask():
            handle_add_drive()
            folders = config_manager.get_folders()
            if not folders:
                return
        else:
            return

    console.print(f"[cyan]Connecting to CloudEye Drive & Gmail engine...[/cyan]")
    try:
        drive_service, gmail_service = auth.get_services()
    except Exception as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        questionary.press_any_key_to_continue().ask()
        return

    console.print(f"[cyan]Scanning {len(folders)} drive(s) and all nested subfolders...[/cyan]")
    with console.status("[bold #00d2ff]Inspecting files and subfolder trees...", spinner="dots"):
        new_files, _, errors = drive_scanner.scan_all_folders(drive_service, folders)

    # Show any access errors
    if errors:
        for fname, err in errors.items():
            console.print(f"[yellow]Warning for '{fname}': {err}[/yellow]")

    if not new_files:
        console.print("\n[bold green][OK] All monitored drives are completely up to date![/bold green]")
        console.print("[dim]No new or modified files found across all nested structures.[/dim]\n")
        if not auto_mode:
            questionary.press_any_key_to_continue("Press any key to return to menu...").ask()
        return

    console.print(f"\n[bold green][OK] Detected {len(new_files)} new or updated file(s) across your drives![/bold green]\n")

    # Send Gmail digest if email configured
    recipient_email = config_manager.get_notification_email()
    if recipient_email:
        with console.status(f"[bold #00d2ff]Sending email digest to {recipient_email}...", spinner="dots"):
            sent = email_notifier.send_update_email(gmail_service, recipient_email, new_files)
        if sent:
            console.print(f"[green][OK] Email alert sent to [bold]{recipient_email}[/bold][/green]")
            cache_manager.mark_files_notified([f["id"] for f in new_files])
        else:
            console.print("[yellow][!] Could not send email alert via Gmail API.[/yellow]")
    else:
        # Prompt user once if they'd like to set their Gmail address
        console.print("[dim]Note: No notification email is currently configured.[/dim]")
        if questionary.confirm("Would you like to set your Gmail address now to receive email alerts?", default=False, style=custom_style).ask():
            new_mail = questionary.text("Enter your Gmail address:", style=custom_style).ask()
            if new_mail and new_mail.strip():
                config_manager.set_notification_email(new_mail.strip())
                recipient_email = new_mail.strip()
                with console.status(f"[bold #00d2ff]Sending email digest to {recipient_email}...", spinner="dots"):
                    email_notifier.send_update_email(gmail_service, recipient_email, new_files)
                console.print(f"[green][OK] Email alert sent to [bold]{recipient_email}[/bold][/green]")

    # Group updates by Drive Alias
    from collections import defaultdict
    drive_groups = defaultdict(list)
    for f in new_files:
        drive_groups[f.get("folder_name", "Monitored Drive")].append(f)

    # Display clean separate table for each drive alias
    choices = []
    for alias, files in drive_groups.items():
        # Sort chronologically (newest published/modified first)
        files.sort(key=lambda x: x.get("modifiedTime", ""), reverse=True)

        table = Table(
            title=f"Updates for Drive: {alias} ({len(files)} new file{'s' if len(files) > 1 else ''})",
            border_style="bright_blue",
            header_style="bold bright_cyan"
        )
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("File Name", style="bold white")
        table.add_column("Subfolder Structure", style="bright_blue")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Published / Modified", style="dim")

        choices.append(questionary.Separator(f"─── Drive: {alias} ({len(files)} updates) ───"))

        for idx, f in enumerate(files, 1):
            mod_time = f.get('modifiedTime', '')[:19].replace('T', ' ')
            sub_display = f.get('subfolder_path') or "[dim]Root[/dim]"
            table.add_row(str(idx), f.get("name"), sub_display, f.get("size_formatted"), mod_time)

            sub_tag = f" > {f.get('subfolder_path')}" if f.get('subfolder_path') else ""
            choices.append(
                questionary.Choice(
                    title=f"{f['name']} ({f['size_formatted']}){sub_tag} - {mod_time}",
                    value=f,
                    checked=True
                )
            )

        console.print(table)
        console.print("")

    # Record discovered files into cache
    cache_manager.record_discovered_files(new_files)

    if auto_mode:
        # Background automated mode: email alert has been sent and cache updated.
        # Exit cleanly without waiting for interactive stdin input.
        return

    # Interactive Checkbox Selection (Space to toggle, Enter to confirm)
    console.print("[bold bright_cyan]Select files to download:[/bold bright_cyan]")
    console.print("[dim]Press [SPACE] to select/deselect items, [ENTER] to confirm downloads.[/dim]\n")

    selected_files = questionary.checkbox(
        "Choose files to download:",
        choices=choices,
        style=custom_style
    ).ask()

    if not selected_files:
        console.print("[dim]No files selected. Exiting update view.[/dim]\n")
        questionary.press_any_key_to_continue().ask()
        return

    # Choose destination strategy
    console.print(f"\n[bold]Selected {len(selected_files)} file(s) for download.[/bold]")
    dest_mode = questionary.select(
        "Download Destination:",
        choices=[
            questionary.Choice("Use each drive's configured destination (preserving subfolder structure)", value="default"),
            questionary.Choice("Specify a custom directory for this download batch", value="custom")
        ],
        style=custom_style
    ).ask()

    custom_dir = None
    if dest_mode == "custom":
        custom_dir = questionary.text(
            "Enter destination folder path:",
            default=os.path.join(os.path.expanduser("~"), "Downloads"),
            style=custom_style
        ).ask().strip()

    # Perform downloads
    console.print("\n[bold bright_cyan]Starting chunked download...[/bold bright_cyan]\n")
    downloaded_count = 0

    for idx, f in enumerate(selected_files, 1):
        target_dir = custom_dir if custom_dir else f.get("default_dest")
        sub_path = f.get("subfolder_path", "")

        console.print(f"[{idx}/{len(selected_files)}] Downloading [bold]{f['name']}[/bold]...")
        success, err, final_path = downloader.download_file(
            drive_service=drive_service,
            file_id=f["id"],
            file_name=f["name"],
            target_dir=target_dir,
            subfolder_path=sub_path,
            total_size=f.get("size", 0)
        )

        if success:
            console.print(f"[green][OK] Saved to: {final_path}[/green]\n")
            downloaded_count += 1
        else:
            console.print(f"[bold red][FAIL] Failed to download '{f['name']}': {err}[/bold red]\n")

    console.print(f"[bold green][OK] Successfully downloaded {downloaded_count} of {len(selected_files)} file(s)![/bold green]\n")
    questionary.press_any_key_to_continue("Press any key to return to menu...").ask()

def handle_all_data():
    console.print("\n[bold bright_cyan]─── All Data: Browse All Drive Files (Categorized by Alias) ───[/bold bright_cyan]\n")

    if not check_credentials_or_guide():
        return

    folders = config_manager.get_folders()
    if not folders:
        console.print("[yellow]No Google Drive folders are currently monitored.[/yellow]")
        if questionary.confirm("Would you like to add a drive to monitor now?", style=custom_style).ask():
            handle_add_drive()
            folders = config_manager.get_folders()
            if not folders:
                return
        else:
            return

    console.print(f"[cyan]Connecting to CloudEye Drive engine...[/cyan]")
    try:
        drive_service, _ = auth.get_services()
    except Exception as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        questionary.press_any_key_to_continue().ask()
        return

    console.print(f"[cyan]Fetching full inventory from {len(folders)} drive(s) and all nested subfolders...[/cyan]")
    with console.status("[bold #00d2ff]Scanning all files across all directories...", spinner="dots"):
        _, all_files, errors = drive_scanner.scan_all_folders(drive_service, folders)

    if errors:
        for fname, err in errors.items():
            console.print(f"[yellow]Warning for '{fname}': {err}[/yellow]")

    if not all_files:
        console.print("\n[yellow]No files found across any of your monitored Google Drive links.[/yellow]\n")
        questionary.press_any_key_to_continue().ask()
        return

    # Check which files have already been downloaded
    downloaded_map = cache_manager.get_downloaded_file_ids()

    # Group all files by Drive Alias
    from collections import defaultdict
    drive_groups = defaultdict(list)
    for f in all_files:
        drive_groups[f.get("folder_name", "Monitored Drive")].append(f)

    console.print(f"[bold green][OK] Loaded {len(all_files)} total file(s) across {len(drive_groups)} drive(s).[/bold green]\n")

    # Display clean separate table for each drive alias, sorted chronologically (newest first)
    choices = []
    for alias, files in drive_groups.items():
        # Sort files in order of publication / modified time (newest first)
        files.sort(key=lambda x: x.get("modifiedTime", ""), reverse=True)

        table = Table(
            title=f"All Data ── Drive: {alias} ({len(files)} total files)",
            border_style="bright_blue",
            header_style="bold bright_cyan"
        )
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("File Name", style="bold white")
        table.add_column("Subfolder Structure", style="bright_blue")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Published / Modified", style="dim")
        table.add_column("Status", justify="center")

        choices.append(questionary.Separator(f"─── Drive: {alias} ({len(files)} files) ───"))

        for idx, f in enumerate(files, 1):
            mod_time = f.get('modifiedTime', '')[:19].replace('T', ' ')
            sub_display = f.get('subfolder_path') or "[dim]Root[/dim]"
            fid = f["id"]
            is_downloaded = fid in downloaded_map
            status_badge = "[cyan]Downloaded[/cyan]" if is_downloaded else "[dim]Available[/dim]"
            table.add_row(str(idx), f.get("name"), sub_display, f.get("size_formatted"), mod_time, status_badge)

            status_tag = "Downloaded" if is_downloaded else "Available"
            sub_tag = f" > {f.get('subfolder_path')}" if f.get('subfolder_path') else ""
            choices.append(
                questionary.Choice(
                    title=f"{f['name']} ({f['size_formatted']}){sub_tag} [{status_tag}] - {mod_time}",
                    value=f,
                    checked=False  # Unchecked by default so user can select specific files
                )
            )

        console.print(table)
        console.print("")

    # Interactive Checkbox Selection (Space to toggle, Enter to confirm)
    console.print("[bold bright_cyan]Download any files at any time:[/bold bright_cyan]")
    console.print("[dim]Press [SPACE] to select/deselect files, [ENTER] to confirm downloads.[/dim]\n")

    selected_files = questionary.checkbox(
        "Choose files to download from All Data:",
        choices=choices,
        style=custom_style
    ).ask()

    if not selected_files:
        console.print("[dim]No files selected. Returning to menu.[/dim]\n")
        questionary.press_any_key_to_continue().ask()
        return

    # Choose destination strategy
    console.print(f"\n[bold]Selected {len(selected_files)} file(s) for download.[/bold]")
    dest_mode = questionary.select(
        "Download Destination:",
        choices=[
            questionary.Choice("Use each drive's configured destination (preserving subfolder structure)", value="default"),
            questionary.Choice("Specify a custom directory for this download batch", value="custom")
        ],
        style=custom_style
    ).ask()

    custom_dir = None
    if dest_mode == "custom":
        custom_dir = questionary.text(
            "Enter destination folder path:",
            default=os.path.join(os.path.expanduser("~"), "Downloads"),
            style=custom_style
        ).ask().strip()

    # Perform downloads
    console.print("\n[bold bright_cyan]Starting chunked download...[/bold bright_cyan]\n")
    downloaded_count = 0

    for idx, f in enumerate(selected_files, 1):
        target_dir = custom_dir if custom_dir else f.get("default_dest")
        sub_path = f.get("subfolder_path", "")

        console.print(f"[{idx}/{len(selected_files)}] Downloading [bold]{f['name']}[/bold]...")
        success, err, final_path = downloader.download_file(
            drive_service=drive_service,
            file_id=f["id"],
            file_name=f["name"],
            target_dir=target_dir,
            subfolder_path=sub_path,
            total_size=f.get("size", 0)
        )

        if success:
            console.print(f"[green][OK] Saved to: {final_path}[/green]\n")
            downloaded_count += 1
        else:
            console.print(f"[bold red][FAIL] Failed to download '{f['name']}': {err}[/bold red]\n")

    console.print(f"[bold green][OK] Successfully downloaded {downloaded_count} of {len(selected_files)} file(s)![/bold green]\n")
    questionary.press_any_key_to_continue("Press any key to return to menu...").ask()

def handle_history():
    console.print("\n[bold bright_cyan]─── Download & Activity History ───[/bold bright_cyan]\n")
    history = cache_manager.get_history(limit=30)
    
    if not history:
        console.print("[dim]No activity history recorded yet.[/dim]\n")
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(
        title="Recent CloudEye Activity & Downloads",
        border_style="bright_blue",
        header_style="bold bright_cyan"
    )
    table.add_column("File Name", style="white")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Detected Date", style="dim")
    table.add_column("Email Alert", justify="center", style="cyan")
    table.add_column("Local Download Path", style="bright_blue")

    for item in history:
        size_str = drive_scanner.format_size(item.get("size", 0))
        seen_str = (item.get("first_seen_at") or "")[:19].replace('T', ' ')
        notified = "Sent" if item.get("notified_at") else "—"
        dl_path = item.get("download_path") or "[dim]Not downloaded[/dim]"
        table.add_row(item.get("name"), size_str, seen_str, notified, dl_path)

    console.print(table)
    console.print("")

    # History submenu for quick utilities
    sub_action = questionary.select(
        "History Options:",
        choices=[
            questionary.Choice("[<] Back to Main Menu", value="back"),
            questionary.Choice("[@] Update Notification Email", value="email"),
            questionary.Choice("[#] View / Remove Monitored Drives", value="drives"),
            questionary.Choice("[!] Clear Database History (.db)", value="clear")
        ],
        style=custom_style
    ).ask()

    if sub_action == "clear":
        if questionary.confirm("Are you sure you want to delete all cached files history from .db?", default=False, style=custom_style).ask():
            count = cache_manager.clear_cache()
            console.print(f"\n[bold green][OK] Successfully deleted {count} record(s) from monitor_cache.db![/bold green]\n")
        else:
            console.print("[dim]Action cancelled.[/dim]\n")
        questionary.press_any_key_to_continue().ask()
    elif sub_action == "email":
        current_email = config_manager.get_notification_email()
        console.print(f"\nCurrent Notification Email: [bold cyan]{current_email or 'Not Set'}[/bold cyan]")
        new_email = questionary.text("Enter new notification Gmail address:", default=current_email, style=custom_style).ask()
        if new_email is not None:
            config_manager.set_notification_email(new_email.strip())
            console.print(f"[bold green][OK] Notification email updated to: {new_email.strip()}[/bold green]\n")
            questionary.press_any_key_to_continue().ask()
    elif sub_action == "drives":
        folders = config_manager.get_folders()
        if not folders:
            console.print("[yellow]No monitored drives saved.[/yellow]\n")
        else:
            choices = [
                questionary.Choice(f"[x] Remove: {f['name']} (Path: {f['default_dest']})", value=f['id'])
                for f in folders
            ]
            choices.append(questionary.Choice("[<] Cancel", value="__cancel__"))
            to_remove = questionary.select("Select drive to remove:", choices=choices, style=custom_style).ask()
            if to_remove and to_remove != "__cancel__":
                config_manager.remove_folder(to_remove)
                console.print("[bold green][OK] Drive removed from monitoring list.[/bold green]\n")
        questionary.press_any_key_to_continue().ask()

def handle_manage_saved_drives():
    while True:
        console.print("\n[bold bright_cyan]─── Manage Saved Drives (Paths & Links) ───[/bold bright_cyan]\n")
        folders = config_manager.get_folders()
        if not folders:
            console.print("[yellow]No monitored drives saved yet.[/yellow]\n")
            if questionary.confirm("Would you like to add a drive now?", style=custom_style).ask():
                handle_add_drive()
                continue
            break

        table = Table(
            title="Saved Monitored Drives",
            border_style="bright_blue",
            header_style="bold bright_cyan"
        )
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Alias Name", style="bold white")
        table.add_column("Folder ID / Link", style="dim")
        table.add_column("Saved Download Path", style="bright_blue")

        for idx, f in enumerate(folders, 1):
            table.add_row(str(idx), f.get("name"), f.get("id"), f.get("default_dest"))

        console.print(table)
        console.print("")

        drive_choices = [
            questionary.Choice(f"[>] {f['name']} -> {f['default_dest']}", value=f)
            for f in folders
        ]
        drive_choices.append(questionary.Choice("[+] Add another drive", value="__add__"))
        drive_choices.append(questionary.Choice("[<] Back to Main Menu", value="__back__"))

        selected = questionary.select(
            "Select a drive to update its path, link, or alias:",
            choices=drive_choices,
            style=custom_style
        ).ask()

        if selected == "__back__" or selected is None:
            break
        elif selected == "__add__":
            handle_add_drive()
            continue

        # Edit selected drive
        target_drive = selected
        fid = target_drive.get("id")
        cur_name = target_drive.get("name")
        cur_url = target_drive.get("url", fid)
        cur_dest = target_drive.get("default_dest")

        edit_action = questionary.select(
            f"What would you like to update for '{cur_name}'?",
            choices=[
                questionary.Choice(f"[1] Update Alias Name (Current: {cur_name})", value="name"),
                questionary.Choice(f"[2] Update Google Drive Link / ID", value="link"),
                questionary.Choice(f"[3] Update Download Destination Path (Current: {cur_dest})", value="path"),
                questionary.Choice(f"[4] Update All (Alias, Link, and Path)", value="all"),
                questionary.Choice(f"[x] Remove this drive from monitoring", value="remove"),
                questionary.Choice("[<] Cancel", value="cancel")
            ],
            style=custom_style
        ).ask()

        if edit_action == "name":
            new_n = questionary.text("Enter new alias name:", default=cur_name, style=custom_style).ask()
            if new_n and new_n.strip():
                config_manager.update_folder(fid, new_name=new_n.strip())
                console.print(f"[bold green][OK] Alias name updated to '{new_n.strip()}'![/bold green]\n")
        elif edit_action == "link":
            new_l = questionary.text("Enter new Google Drive Link or Folder ID:", default=cur_url, style=custom_style).ask()
            if new_l and new_l.strip():
                new_fid = extract_folder_id(new_l)
                if new_fid:
                    config_manager.update_folder(fid, new_url_or_id=new_l.strip())
                    console.print(f"[bold green][OK] Drive link updated to ID: {new_fid}![/bold green]\n")
                else:
                    console.print("[bold red]Invalid Google Drive link or ID.[/bold red]\n")
        elif edit_action == "path":
            new_p = questionary.text("Enter new local download path:", default=cur_dest, style=custom_style).ask()
            if new_p and new_p.strip():
                config_manager.update_folder(fid, new_dest=new_p.strip())
                console.print(f"[bold green][OK] Download path updated to '{new_p.strip()}'![/bold green]\n")
        elif edit_action == "all":
            new_n = questionary.text("Enter alias name:", default=cur_name, style=custom_style).ask()
            new_l = questionary.text("Enter Google Drive link or ID:", default=cur_url, style=custom_style).ask()
            new_p = questionary.text("Enter download path:", default=cur_dest, style=custom_style).ask()
            config_manager.update_folder(
                fid,
                new_name=new_n.strip() if new_n else None,
                new_url_or_id=new_l.strip() if new_l else None,
                new_dest=new_p.strip() if new_p else None
            )
            console.print("[bold green][OK] Drive configuration updated successfully![/bold green]\n")
        elif edit_action == "remove":
            if questionary.confirm(f"Are you sure you want to remove '{cur_name}'?", default=False, style=custom_style).ask():
                config_manager.remove_folder(fid)
                console.print(f"[bold green][OK] Removed '{cur_name}' from monitoring list.[/bold green]\n")

        questionary.press_any_key_to_continue().ask()

def handle_update_username():
    console.print("\n[bold bright_cyan]─── Update Username ───[/bold bright_cyan]\n")
    current_username = config_manager.get_username()
    console.print(f"Current Username: [bold cyan]{current_username or 'Not Set'}[/bold cyan]\n")

    new_name = questionary.text(
        "Enter your new username:",
        default=current_username,
        style=custom_style
    ).ask()

    if new_name is not None and new_name.strip():
        config_manager.set_username(new_name.strip())
        console.print(f"\n[bold green][OK] Username successfully updated to: '{new_name.strip()}'![/bold green]\n")
    else:
        console.print("[dim]No changes made.[/dim]\n")

    questionary.press_any_key_to_continue("Press any key to return to menu...").ask()

def handle_change_email():
    console.print("\n[bold bright_cyan]─── Change Notification Email ───[/bold bright_cyan]\n")
    current_email = config_manager.get_notification_email()
    console.print(f"Current Alert Email: [bold cyan]{current_email or 'Not Set'}[/bold cyan]\n")

    new_email = questionary.text(
        "Enter new Gmail address to receive alert digests:",
        default=current_email,
        style=custom_style
    ).ask()

    if new_email is not None and new_email.strip():
        config_manager.set_notification_email(new_email.strip())
        console.print(f"\n[bold green][OK] Notification email successfully updated to: {new_email.strip()}[/bold green]\n")
    else:
        console.print("[dim]No changes made.[/dim]\n")

    questionary.press_any_key_to_continue("Press any key to return to menu...").ask()

def handle_background_scheduler():
    console.print("\n[bold bright_cyan]─── Background Auto-Monitoring (Windows Scheduler) ───[/bold bright_cyan]\n")
    info = scheduler_manager.get_task_info()
    is_active = info.get("configured", False) and info.get("status") == "Active"

    if is_active:
        console.print(f"Status: [bold green]● Active (Running in Background)[/bold green]")
        if "next_run" in info:
            console.print(f"Next Scheduled Run: [cyan]{info['next_run']}[/cyan]")
    else:
        console.print(f"Status: [bold yellow]○ Inactive (Not currently running in background)[/bold yellow]")

    console.print("\n[dim]When active, CloudEye silently scans your Google Drives in the background[/dim]")
    console.print("[dim]and automatically sends an email alert as soon as any updates are detected.[/dim]\n")

    choices = []
    if is_active:
        choices.append(questionary.Choice("[1] Change check interval frequency", value="change"))
        choices.append(questionary.Choice("[!] Disable / Turn off background auto-monitoring", value="disable"))
    else:
        choices.append(questionary.Choice("[+] Enable background auto-monitoring", value="enable"))

    choices.append(questionary.Choice("[<] Back to Main Menu", value="back"))

    action = questionary.select("Select option:", choices=choices, style=custom_style).ask()

    if action in ["enable", "change"]:
        interval = questionary.select(
            "How often should CloudEye check for updates in the background?",
            choices=[
                questionary.Choice("Every 30 minutes", value=30),
                questionary.Choice("Every 1 hour (Recommended)", value=60),
                questionary.Choice("Every 2 hours", value=120),
                questionary.Choice("Every 4 hours", value=240),
            ],
            style=custom_style
        ).ask()

        if interval:
            ok, msg = scheduler_manager.register_background_task(interval)
            if ok:
                console.print(f"\n[bold green][OK] {msg}[/bold green]\n")
            else:
                console.print(f"\n[bold red][FAIL] {msg}[/bold red]\n")
    elif action == "disable":
        if questionary.confirm("Turn off background auto-monitoring?", default=True, style=custom_style).ask():
            ok, msg = scheduler_manager.remove_background_task()
            if ok:
                console.print(f"\n[bold green][OK] {msg}[/bold green]\n")
            else:
                console.print(f"\n[bold red][FAIL] {msg}[/bold red]\n")

    questionary.press_any_key_to_continue().ask()

def main():
    parser = argparse.ArgumentParser(description="CloudEye - Google Drive Monitor & Deep Structure Sync Engine")
    parser.add_argument("--check", "-c", action="store_true", help="Directly check for updates and exit")
    args = parser.parse_args()

    cache_manager.init_db()

    if args.check:
        handle_view_updates(auto_mode=True)
        return

    # Ensure user name is set
    username = ensure_user_onboarding()

    while True:
        display_banner(username)

        # Dynamic badge indicating background task status
        is_bg_active = scheduler_manager.is_task_scheduled()
        bg_badge = "[ON]" if is_bg_active else "[OFF]"
        
        choice = questionary.select(
            "Select an action:",
            choices=[
                questionary.Choice("[+]  Add new drive to monitor", value="add"),
                questionary.Choice("[*]  View updates & download", value="updates"),
                questionary.Choice("[D]  All Data (Browse & download any file)", value="alldata"),
                questionary.Choice("[#]  Manage saved drives (paths & links)", value="drives"),
                questionary.Choice(f"[A]  Auto-monitor in background {bg_badge}", value="auto"),
                questionary.Choice("[i]  History of downloading", value="history"),
                questionary.Choice("[u]  Update username", value="username"),
                questionary.Choice("[@]  Change notification email", value="email"),
                questionary.Choice("[x]  Exit CloudEye", value="exit")
            ],
            style=custom_style
        ).ask()

        if choice == "add":
            handle_add_drive()
        elif choice == "updates":
            handle_view_updates()
        elif choice == "alldata":
            handle_all_data()
        elif choice == "drives":
            handle_manage_saved_drives()
        elif choice == "auto":
            handle_background_scheduler()
        elif choice == "history":
            handle_history()
        elif choice == "username":
            handle_update_username()
            username = config_manager.get_username()
        elif choice == "email":
            handle_change_email()
        elif choice == "exit" or choice is None:
            console.print("\n[bold bright_cyan]Thank you for using CloudEye. Goodbye![/bold bright_cyan]\n")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]CloudEye stopped by user. Exiting...[/yellow]")
        sys.exit(0)
