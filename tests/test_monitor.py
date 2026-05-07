import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import socket

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
    @patch('monitor.socket.create_connection')
    def test_health_normal_no_action(self, mock_create_connection, mock_ssh_client):
        # Mock reachability
        mock_create_connection.return_value = MagicMock()
        mock_ssh_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_instance
        
        # Fake the stdout from the 'ps' command
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'1\n'
        mock_ssh_instance.exec_command.return_value = (None, mock_stdout, None)

        # Execute: Run our health check
        monitor.check_udm_health()

        # Assert: It should check the zombie count and log normal health, but not restart
        self.assertEqual(mock_ssh_instance.exec_command.call_count, 2)
        mock_ssh_instance.exec_command.assert_any_call('logger -t healthy-udm "Detected 1 zombie processes. System health normal."')
        mock_create_connection.assert_called_once_with(('192.168.1.1', 22), timeout=2)

    @patch('monitor.paramiko.SSHClient')
    @patch('monitor.socket.create_connection')
    def test_health_threshold_exceeded_triggers_restart(self, mock_create_connection, mock_ssh_client):
        # Mock reachability
        mock_create_connection.return_value = MagicMock()
        mock_ssh_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_instance
        
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'15\n'
        mock_ssh_instance.exec_command.return_value = (None, mock_stdout, None)

        # Execute: Run the health check
        monitor.check_udm_health()

        # Assert: It checked the count, logged the problem, and restarted the service
        self.assertEqual(mock_ssh_instance.exec_command.call_count, 3)
        mock_ssh_instance.exec_command.assert_any_call('unifi-os restart')

    @patch('monitor.paramiko.SSHClient')
    @patch('monitor.socket.create_connection')
    def test_unreachable_udm_skips_health_check(self, mock_create_connection, mock_ssh_client):
        # Simulate unreachable UDM SSH port
        mock_create_connection.side_effect = socket.timeout
        mock_ssh_instance = MagicMock()
        mock_ssh_client.return_value = mock_ssh_instance

        monitor.check_udm_health()

        # Assert: no SSH connection attempt or exec_command calls were made
        mock_ssh_instance.connect.assert_not_called()
        mock_ssh_instance.exec_command.assert_not_called()
        mock_create_connection.assert_called_once_with(('192.168.1.1', 22), timeout=2)

if __name__ == '__main__':
    unittest.main()

