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
        monitor.ZOMBIE_THRESHOLD = 2

    @patch('monitor.paramiko.SSHClient')
    def test_health_normal_no_action(self, mock_ssh_client):
        # 1. SETUP: Fake an SSH connection that returns exactly 2 zombies
        mock_ssh_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_instance
        
        # Fake the stdout from the 'ps' command
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'2\n'
        mock_ssh_instance.exec_command.return_value = (None, mock_stdout, None)

        # 2. EXECUTE: Run our health check
        monitor.check_udm_health()

        # 3. ASSERT: Prove that it did NOT try to restart the UDM
        # It should only call exec_command once (to check the count)
        self.assertEqual(mock_ssh_instance.exec_command.call_count, 1)

    @patch('monitor.paramiko.SSHClient')
    def test_health_threshold_exceeded_triggers_restart(self, mock_ssh_client):
        # 1. SETUP: Fake an SSH connection that returns 15 zombies (Above threshold)
        mock_ssh_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_instance
        
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'15\n'
        mock_ssh_instance.exec_command.return_value = (None, mock_stdout, None)

        # 2. EXECUTE: Run the health check
        monitor.check_udm_health()

        # 3. ASSERT: Prove it ran the restart commands
        self.assertEqual(mock_ssh_instance.exec_command.call_count, 2) # 1 check + 1 log + 1 restart
        
        # Verify the specific restart command was issued
        mock_ssh_instance.exec_command.assert_any_call('unifi-os restart')

    if __name__ == '__main__':
