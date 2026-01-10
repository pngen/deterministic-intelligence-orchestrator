"""
Unit tests for the DeterminismTracker.
"""

import unittest
from dio.core.determinism import DeterminismTracker


class TestDeterminismTracker(unittest.TestCase):
    
    def test_record_deterministic_node(self):
        """Test recording deterministic nodes."""
        tracker = DeterminismTracker()
        
        tracker.record_deterministic_node("node1")
        tracker.record_deterministic_node("node2")
        
        summary = tracker.get_determinism_summary()
        self.assertIn("node1", summary["deterministic"])
        self.assertIn("node2", summary["deterministic"])
        
    def test_record_bounded_nondeterministic_node(self):
        """Test recording bounded nondeterministic nodes."""
        tracker = DeterminismTracker()
        
        tracker.record_bounded_nondeterministic_node("node1")
        tracker.record_bounded_nondeterministic_node("node2")
        
        summary = tracker.get_determinism_summary()
        self.assertIn("node1", summary["bounded_nondeterministic"])
        self.assertIn("node2", summary["bounded_nondeterministic"])
        
    def test_record_external_nondeterministic_node(self):
        """Test recording external nondeterministic nodes."""
        tracker = DeterminismTracker()
        
        tracker.record_external_nondeterministic_node("node1")
        tracker.record_external_nondeterministic_node("node2")
        
        summary = tracker.get_determinism_summary()
        self.assertIn("node1", summary["external_nondeterministic"])
        self.assertIn("node2", summary["external_nondeterministic"])
        
    def test_get_determinism_summary(self):
        """Test getting determinism summary."""
        tracker = DeterminismTracker()
        
        tracker.record_deterministic_node("deterministic_node")
        tracker.record_bounded_nondeterministic_node("bounded_node")
        tracker.record_external_nondeterministic_node("external_node")
        
        summary = tracker.get_determinism_summary()
        
        self.assertIn("deterministic_node", summary["deterministic"])
        self.assertIn("bounded_node", summary["bounded_nondeterministic"])
        self.assertIn("external_node", summary["external_nondeterministic"])
        
    def test_hash(self):
        """Test determinism tracker hashing."""
        tracker1 = DeterminismTracker()
        tracker1.record_deterministic_node("node1")
        
        tracker2 = DeterminismTracker()
        tracker2.record_deterministic_node("node1")
        
        hash1 = tracker1.hash()
        hash2 = tracker2.hash()
        
        self.assertEqual(hash1, hash2)


if __name__ == '__main__':
    unittest.main()