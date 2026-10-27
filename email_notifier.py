import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict, Any, Tuple

def create_email_content(new_files: List[Dict[str, Any]]) -> Tuple[str, str]:
    """Generates (plain_text, html) representation for new files notification."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = len(new_files)

    # Plain Text Version
    plain_lines = [
        f"Google Drive Monitor - Update Notification",
        f"Scan Time: {now_str}",
        f"Total New/Updated Files: {count}",
        "=" * 50,
        ""
    ]
    for idx, f in enumerate(new_files, 1):
        folder_display = f"{f.get('folder_name')} / {f.get('subfolder_path')}" if f.get('subfolder_path') else f.get('folder_name')
        plain_lines.append(f"{idx}. {f.get('name')}")
        plain_lines.append(f"   Folder: {folder_display}")
        plain_lines.append(f"   Size: {f.get('size_formatted')}")
        plain_lines.append(f"   Modified: {f.get('modifiedTime', 'N/A')}")
        if f.get("webViewLink"):
            plain_lines.append(f"   Link: {f.get('webViewLink')}")
        plain_lines.append("-" * 30)

    plain_lines.append("\nOpen your terminal to select and download these files.")
    plain_text = "\n".join(plain_lines)

    # HTML Version (Modern responsive card design)
    rows_html = ""
    for idx, f in enumerate(new_files, 1):
        link_btn = (
            f'<a href="{f.get("webViewLink")}" style="color: #2563eb; text-decoration: none; font-weight: 500;">Open Drive ↗</a>'
            if f.get("webViewLink") else "—"
        )
        rows_html += f"""
        <tr style="border-bottom: 1px solid #e5e7eb; font-size: 14px;">
            <td style="padding: 12px; font-weight: 600; color: #1f2937;">{idx}</td>
            <td style="padding: 12px; color: #111827; font-weight: 600;">{f.get('name')}</td>
            <td style="padding: 12px; color: #4b5563;">{f.get('folder_name')}{f" / {f.get('subfolder_path')}" if f.get('subfolder_path') else ""}</td>
            <td style="padding: 12px; color: #4b5563;">{f.get('size_formatted')}</td>
            <td style="padding: 12px; color: #6b7280; font-size: 13px;">{f.get('modifiedTime', 'N/A')[:19].replace('T', ' ')}</td>
            <td style="padding: 12px;">{link_btn}</td>
        </tr>
        """

    html_text = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 24px; color: #374151;">
        <div style="max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden; border: 1px solid #e5e7eb;">
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 24px 32px; color: white;">
                <h1 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">🔔 Google Drive Monitor Alert</h1>
                <p style="margin: 6px 0 0 0; opacity: 0.9; font-size: 14px;">Scan completed on {now_str}</p>
            </div>
            
            <div style="padding: 24px 32px;">
                <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px;">
                    <strong style="color: #1e40af; font-size: 15px;">{count} new or updated file(s)</strong> detected in your monitored Google Drive folders.
                </div>

                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="background-color: #f9fafb; border-bottom: 2px solid #e5e7eb; font-size: 12px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.5px;">
                            <th style="padding: 10px 12px;">#</th>
                            <th style="padding: 10px 12px;">File Name</th>
                            <th style="padding: 10px 12px;">Folder</th>
                            <th style="padding: 10px 12px;">Size</th>
                            <th style="padding: 10px 12px;">Modified</th>
                            <th style="padding: 10px 12px;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>

                <div style="margin-top: 32px; padding: 16px; background-color: #f9fafb; border-radius: 8px; font-size: 13px; color: #6b7280; text-align: center;">
                    💡 You can download any of these files directly using your interactive terminal program.
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return plain_text, html_text

def send_update_email(gmail_service, to_email: str, new_files: List[Dict[str, Any]]) -> bool:
    """
    Sends an update email using the Gmail API.
    Returns True if successful, False otherwise.
    """
    if not to_email or not new_files:
        return False

    try:
        subject = f"🔔 Google Drive Monitor: {len(new_files)} New Update(s) Detected"
        plain_text, html_text = create_email_content(new_files)

        message = MIMEMultipart("alternative")
        message["to"] = to_email
        message["subject"] = subject

        part1 = MIMEText(plain_text, "plain", "utf-8")
        part2 = MIMEText(html_text, "html", "utf-8")

        message.attach(part1)
        message.attach(part2)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_body = {"raw": raw_message}

        gmail_service.users().messages().send(userId="me", body=send_body).execute()
        return True
    except Exception as e:
        print(f"\n[Warning] Failed to send email via Gmail API: {e}")
        return False
