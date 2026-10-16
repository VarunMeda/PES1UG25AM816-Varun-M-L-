"""Tests for the Lab 5 fare calculator."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))
import fare_calculator as fare  # noqa: E402


class FareCalculatorTests(unittest.TestCase):
    def setUp(self):
        fare.cards.clear()

    def test_distance_boundaries(self):
        self.assertEqual(fare.fare_for_distance(0), 10)
        self.assertEqual(fare.fare_for_distance(2), 20)
        self.assertEqual(fare.fare_for_distance(32), 60)

    def test_peak_and_concessions(self):
        self.assertTrue(fare.is_peak("08:00"))
        self.assertFalse(fare.is_peak("14:00"))
        self.assertEqual(fare.journey_fare(10, "14:00", ["student", "senior"]), 10.12)

    def test_daily_cap(self):
        journeys = [(30, "08:15", []), (30, "18:30", []), (40, "21:00", [])]
        self.assertEqual(fare.daily_total(journeys), fare.DAILY_CAP)

    def test_card_issue_tap_and_top_up(self):
        fare.issue_card("C1", 60)
        self.assertEqual(fare.tap_out("C1", 30, "09:00"), 10.0)
        self.assertEqual(fare.top_up("C1", 5), 15.0)
        with self.assertRaises(ValueError):
            fare.tap_out("missing", 2, "09:00")

    def test_card_rejects_invalid_operations(self):
        fare.issue_card("C1", 1)
        with self.assertRaises(ValueError):
            fare.tap_out("C1", 30, "09:00")
        with self.assertRaises(ValueError):
            fare.top_up("C1", 0)

    def test_route_and_checksum(self):
        self.assertEqual(fare.cheapest_route([12, 5, 21]), 5)
        self.assertEqual(len(fare.ticket_checksum("C1|30km|09:00")), 64)

    def test_safe_xml_loading_and_entity_rejection(self):
        xml = "<line><stop name='Central'/><stop name='Market'/></line>"
        self.assertEqual(fare.load_stops(xml), ["Central", "Market"])
        malicious = "<!DOCTYPE line [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><line>"
        malicious += "<stop name='&xxe;'/></line>"
        with self.assertRaises(Exception):
            fare.load_stops(malicious)

    @patch("fare_calculator.paramiko.SSHClient")
    def test_ssh_requires_host_key_verification(self, ssh_client):
        client = ssh_client.return_value
        client.get_transport.return_value = MagicMock()
        channel = client.get_transport.return_value.open_session.return_value
        channel.recv_exit_status.return_value = 0
        sftp = client.open_sftp.return_value.__enter__.return_value
        fare.push_fares_to_gate("gate.example", "fares.txt", "known_hosts")
        client.load_host_keys.assert_called_once_with("known_hosts")
        client.set_missing_host_key_policy.assert_called_once()
        self.assertIsInstance(
            client.set_missing_host_key_policy.call_args.args[0],
            fare.paramiko.RejectPolicy,
        )
        sftp.put.assert_called_once_with("fares.txt", "/var/lib/transit-fares.txt")


if __name__ == "__main__":
    unittest.main()
