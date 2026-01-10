"""
Unit tests for the ExecutionTranscript.
"""

import unittest
from datetime import datetime, timezone
from dio.core.transcript import ExecutionTranscript, TranscriptEntry, EntryType


class TestExecutionTranscript(unittest.TestCase):
    
    def test_add_entry(self):
        """Test adding an entry to a transcript."""
        transcript = ExecutionTranscript(
            execution_id="test_execution",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        entry = TranscriptEntry(
            entry_type=EntryType.SUBMISSION,
            timestamp=datetime.now(timezone.utc),
            data={"message": "Test submission"}
        )
        
        transcript.add_entry(entry)
        self.assertEqual(len(transcript.entries), 1)
        
    def test_verify_integrity(self):
        """Test transcript integrity verification."""
        transcript = ExecutionTranscript(
            execution_id="test_execution",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Empty transcript should be valid
        self.assertTrue(transcript.verify_integrity())
        
        # Add an entry
        entry = TranscriptEntry(
            entry_type=EntryType.SUBMISSION,
            timestamp=datetime.now(timezone.utc),
            data={"message": "Test submission"}
        )
        transcript.add_entry(entry)
        
        # Should still be valid
        self.assertTrue(transcript.verify_integrity())
        
    def test_get_entries_by_type(self):
        """Test getting entries by type."""
        transcript = ExecutionTranscript(
            execution_id="test_execution",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        entry1 = TranscriptEntry(
            entry_type=EntryType.SUBMISSION,
            timestamp=datetime.now(timezone.utc),
            data={"message": "Test submission"}
        )
        
        entry2 = TranscriptEntry(
            entry_type=EntryType.NODE_START,
            timestamp=datetime.now(timezone.utc),
            data={"node_id": "test_node"}
        )
        
        transcript.add_entry(entry1)
        transcript.add_entry(entry2)
        
        # Get submission entries
        submissions = transcript.get_entries_by_type(EntryType.SUBMISSION)
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0], entry1)
        
    def test_get_node_entries(self):
        """Test getting entries for a specific node."""
        transcript = ExecutionTranscript(
            execution_id="test_execution",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        entry1 = TranscriptEntry(
            entry_type=EntryType.NODE_START,
            timestamp=datetime.now(timezone.utc),
            data={"node_id": "test_node"}
        )
        
        entry2 = TranscriptEntry(
            entry_type=EntryType.NODE_COMPLETE,
            timestamp=datetime.now(timezone.utc),
            data={"node_id": "other_node"}
        )
        
        transcript.add_entry(entry1)
        transcript.add_entry(entry2)
        
        # Get entries for test_node
        node_entries = transcript.get_node_entries("test_node")
        self.assertEqual(len(node_entries), 1)
        self.assertEqual(node_entries[0], entry1)
        
    def test_hash(self):
        """Test transcript hashing."""
        timestamp = datetime.now(timezone.utc)
        
        transcript1 = ExecutionTranscript(
            execution_id="test_execution",
            graph_hash="test_hash",
            timestamp=timestamp
        )
        
        transcript2 = ExecutionTranscript(
            execution_id="test_execution",
            graph_hash="test_hash",
            timestamp=timestamp
        )
        
        hash1 = transcript1.hash()
        hash2 = transcript2.hash()
        
        self.assertEqual(hash1, hash2)
        
    def test_sign_and_verify_signature(self):
        """Test signing and verifying transcript signatures."""
        timestamp = datetime.now(timezone.utc)
        transcript = ExecutionTranscript(
            execution_id="test_execution",
            graph_hash="test_hash",
            timestamp=timestamp
        )
        
        # Test without signature
        self.assertFalse(transcript.verify_signature(b"test_key"))
        
        # Sign the transcript
        signing_key = b"test_signing_key_1234567890"
        transcript.sign(signing_key)
        
        # Verify signature
        self.assertTrue(transcript.verify_signature(signing_key))
        
        # Verify with wrong key
        self.assertFalse(transcript.verify_signature(b"wrong_key"))


if __name__ == '__main__':
    unittest.main()