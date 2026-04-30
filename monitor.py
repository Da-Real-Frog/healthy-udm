import os
import time
import paramiko

# --- Configuration Variables ---
# These are pulled from the docker-compose.yml environment variables
UDM_IP = os.getenv('UDM_IP')
SSH_USER = os.getenv('SSH_USER')
SSH_PASS = os.getenv('SSH_PASS')

ZOMBIE_THRESHOLD = int(os.getenv('ZOMBIE_THRESHOLD', 2))
CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', 3600)) # Default: 1 hour

def check_udm_health():
    """Connects to UDM, checks for zombies, and restarts services if needed."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to UDM at {UDM_IP}...")
        client.connect(
            hostname=UDM_IP,
            username=SSH_USER,
            password=SSH_PASS,
            #timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
        print(f"User name: {SSH_USER}")
        print(f"password: {SSH_PASS}")
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
            print("Restart command issued. Wrote in the log")
        else:
            # 1. Add an entry to the UDM's own internal system log (syslog)
            client.exec_command(f'logger -t healthy-udm "Detected {zombie_count} zombie processes. System health normal."')
            print("System health normal. No action required. Wrote in the log")

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
