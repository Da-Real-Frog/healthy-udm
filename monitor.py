import os
import time
import smtplib
import paramiko
from email.message import EmailMessage

# --- Configuration Variables ---
# These are pulled from the docker-compose.yml environment variables
UDM_IP = os.getenv('UDM_IP')
SSH_USER = os.getenv('SSH_USER')
SSH_PASS = os.getenv('SSH_PASS')

SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
NOTIFY_EMAIL = os.getenv('NOTIFY_EMAIL')

ZOMBIE_THRESHOLD = int(os.getenv('ZOMBIE_THRESHOLD', 10))
CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', 3600)) # Default: 1 hour

def send_email_alert(zombie_count):
    """Sends an email notification when action is taken."""
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL]):
        print("SMTP credentials incomplete. Skipping email notification.")
        return

    try:
        msg = EmailMessage()
        msg.set_content(f"The UDM Health Monitor detected {zombie_count} zombie processes.\n\n"
                        f"The 'unifi-os' service has been successfully restarted to clear the locked resources.")
        msg['Subject'] = 'UDM Alert: Zombie Processes Cleared'
        msg['From'] = SMTP_USER
        msg['To'] = NOTIFY_EMAIL

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print("Alert email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_udm_health():
    """Connects to UDM, checks for zombies, and restarts services if needed."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to UDM at {UDM_IP}...")
        client.connect(hostname=UDM_IP, username=SSH_USER, password=SSH_PASS, timeout=10)
        
        # Command to count zombie processes in Debian/UniFi OS
        stdin, stdout, stderr = client.exec_command("ps -eo stat | grep -c '^Z'")
        zombie_count = int(stdout.read().decode('utf-8').strip())
        
        print(f"Current zombie process count: {zombie_count}")

        if zombie_count >= ZOMBIE_THRESHOLD:
            print(f"Threshold exceeded! Attempting to restart unifi-os...")
            
            # 1. Add an entry to the UDM's own internal system log (syslog)
            client.exec_command(f'logger -t healthy-udm "Detected {zombie_count} zombie processes. Restarting unifi-os."')
            
            # 2. Restart the UniFi OS service to clear the locked Java resources
            client.exec_command('unifi-os restart')
            print("Restart command issued.")
            
            # 3. Send the email notification
            send_email_alert(zombie_count)
        else:
            print("System health normal. No action required.")

    except Exception as e:
        print(f"Error connecting to or interrogating UDM: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("Starting UDM Health Monitor...")
    while True:
        check_udm_health()
        print(f"Sleeping for {CHECK_INTERVAL_SECONDS} seconds...")
        time.sleep(CHECK_INTERVAL_SECONDS)
