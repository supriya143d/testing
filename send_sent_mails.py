#!/usr/bin/env python3
"""
send_recruiters_drive_resume_dedup_debug_with_history.py
"""

import os
import csv
import time
import smtplib
import argparse
import requests
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


# ---------- CONFIGURABLE FIELDS ----------
SENDER_NAME  = "Supriya Gowra"
SENDER_EMAIL = "supriyasuppug98@gmail.com"
APP_PASSWORD = "jngm hjsz epxn gjld"  # <-- Gmail App Password

SUBJECT_TEMPLATE = "Applying for DevOps Engineer position"

BODY_TEMPLATE = """Hi {name},

Trust you are doing well!

1. Total Experience: 4+ yrs
2. Notice Period: Immediate Joiner

Please find the attached resume for your reference and below details.
If anything else is required, please let me know.

I recently came across a DevOps position on LinkedIn and wanted to explore if my background aligns with the role.
I would greatly appreciate it if you could take a moment to review it and let me know if it could be a fit.
Thank you for your time and consideration.

I am eagerly waiting for new opportunities.

Thanks & Regards,
Supriya Gowra
8125336081
LinkedIn: https://www.linkedin.com/in/supriyagowra
"""
# -----------------------------------------


# ---------- NEW FUNCTIONS ADDED ----------
def load_sent_emails(path="sent_emails.txt"):
    """Load previously sent emails to avoid duplicates."""
    if not os.path.exists(path):
        return set()
    with open(path, "r") as f:
        return set(line.strip().lower() for line in f if line.strip())


def save_sent_email(email, path="sent_emails.txt"):
    """Record newly sent email."""
    with open(path, "a") as f:
        f.write(email.lower() + "\n")
# -----------------------------------------


def download_from_drive(drive_link: str, output_path: Path):
    print("Downloading resume from Google Drive...")
    try:
        if "id=" in drive_link:
            file_id = drive_link.split("id=")[1].split("&")[0]
        elif "/d/" in drive_link:
            file_id = drive_link.split("/d/")[1].split("/")[0]
        else:
            raise ValueError("Invalid Google Drive link format")

        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            output_path.write_bytes(response.content)
            print(f"✅ Resume downloaded: {output_path}")
        else:
            raise RuntimeError(f"Failed to download (status {response.status_code})")
    except Exception as e:
        print(f"❌ Error downloading from Google Drive: {e}")
        exit(1)


def attach_file(msg, path):
    with open(path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    custom_name = "Supriya G.pdf"
    part.add_header("Content-Disposition", f'attachment; filename="{custom_name}"')
    msg.attach(part)


def send_email(server, sender_name, sender_email, recipient, subject, body, attachment_path):
    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    attach_file(msg, attachment_path)
    server.send_message(msg)


def load_recruiters(csv_path: Path):
    with csv_path.open(newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return []

    if "email" in [c.lower() for c in rows[0]]:
        rows = rows[1:]

    recruiters = []
    for row in rows:
        if len(row) < 2:
            continue
        name, email = row[0].strip(), row[1].strip().lower()
        if not name:
            name = email.split("@")[0].split(".")[0].capitalize()
        recruiters.append((name, email))
    return recruiters


def main():
    parser = argparse.ArgumentParser(description="Send DevOps emails with resume downloaded from Drive.")
    parser.add_argument("--csv", required=True, help="Path to recruiters.csv (name,email).")
    parser.add_argument("--drive-link", required=True, help="Google Drive shareable link of resume.")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between emails (seconds).")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    recruiters = load_recruiters(csv_path)

    if not recruiters:
        print("No recruiters found in CSV.")
        return

    # Load past sent emails
    sent_history = load_sent_emails()
    print(f"📘 Loaded {len(sent_history)} previously sent emails.\n")

    # Deduplicate CSV list
    seen = set()
    unique = []
    for name, email in recruiters:
        if email in seen:
            print(f"⚠️ Duplicate in CSV skipped: {email}")
            continue
        seen.add(email)
        unique.append((name, email))

    print(f"Total unique recruiters in CSV: {len(unique)}\n")

    # Download resume
    resume_path = Path("supriya.pdf")
    download_from_drive(args.drive_link, resume_path)

    print("Connecting to Gmail SMTP server...")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            print("Logging in...")
            server.login(SENDER_EMAIL, APP_PASSWORD)
            print(f"✅ Logged in as {SENDER_EMAIL}\n")

            for i, (name, email) in enumerate(unique, start=1):

                # 🔥 NEW: Skip if email already sent
                if email in sent_history:
                    print(f"[{i}] ⏭️ Already sent earlier → Skipping {email}")
                    continue

                body = BODY_TEMPLATE.format(name=name)

                try:
                    send_email(server, SENDER_NAME, SENDER_EMAIL, email, SUBJECT_TEMPLATE, body, resume_path)
                    print(f"[{i}] ✅ Sent → {email}")

                    # Save this email to history
                    save_sent_email(email)

                except Exception as e:
                    print(f"[{i}] ❌ Failed: {email} → {e}")

                time.sleep(args.delay)

        print("\n🎉 All Emails Processed!")

    except Exception as e:
        print("❌ Unexpected error:", e)

    finally:
        if resume_path.exists():
            resume_path.unlink()


if __name__ == "__main__":
    main()
