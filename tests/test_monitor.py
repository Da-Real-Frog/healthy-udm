import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to the path so it can find monitor.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import monitor

class TestUDMMonitor(unittest.TestCase):

    def setUp(self):
        # Temporarily override the environment variables for testing
        monitor.UDM_IP = '192.168.1.1'
        monitor.SSH_USER = 'root'
        monitor.SSH_PASS = 'testpass'
        monitor.ZOMBIE_THRESHOLD = 10
        monitor.SMTP_SERVER = 'smtp.test.com'
        monitor.SMTP_USER = 'testuser'
        monitor.SMTP_PASS = 'testpass'
        monitor.NOTIFY_EMAIL = 'admin@test.com'

    @patch('monitor.paramiko.SSHClient')
    @patch('monitor.send_email_alert')
    def test_health_normal_no_action(self, mock_send_email, mock_ssh_client):
        # 1. SETUP: Fake an SSH connection that returns exactly 2 zombies
        mock_ssh_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_instance
        
        # Fake the stdout from the 'ps' command
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'2\n'
        mock_ssh_instance.exec_command.return_value = (None, mock_stdout, None)

        # 2. EXECUTE: Run our health check
        monitor.check_udm_health()

        # 3. ASSERT: Prove that it did NOT try to restart the UDM or send an email
        # It should only call exec_command once (to check the count)
        self.assertEqual(mock_ssh_instance.exec_command.call_count, 1)
        mock_send_email.assert_not_called()

    @patch('monitor.paramiko.SSHClient')
    @patch('monitor.send_email_alert')
    def test_health_threshold_exceeded_triggers_restart(self, mock_send_email, mock_ssh_client):
        # 1. SETUP: Fake an SSH connection that returns 15 zombies (Above threshold)
        mock_ssh_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_instance
        
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'15\n'
        mock_ssh_instance.exec_command.return_value = (None, mock_stdout, None)

        # 2. EXECUTE: Run the health check
        monitor.check_udm_health()

        # 3. ASSERT: Prove it ran the restart commands and tried to email
        self.assertEqual(mock_ssh_instance.exec_command.call_count, 3) # 1 check + 1 log + 1 restart
        
        # Verify the specific restart command was issued
        mock_ssh_instance.exec_command.assert_any_call('unifi-os restart')
        
        # Verify the email alert function was triggered
        mock_send_email.assert_called_once_with(15)

    @patch('monitor.smtplib.SMTP')
    def test_email_sending_logic(self, mock_smtp):
        # 1. SETUP: Fake the Mail Server
        mock_server_instance = MagicMock()
        mock_smtp.return_value = mock_server_instance

        # 2. EXECUTE: Trigger the email function
        monitor.send_email_alert(12)

        # 3. ASSERT: Prove it logged in and sent the message securely
        mock_server_instance.starttls.assert_called_once()
        mock_server_instance.login.assert_called_once_with('testuser', 'testpass')
        mock_server_instance.send_message.assert_called_once()
        mock_server_instance.quit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
