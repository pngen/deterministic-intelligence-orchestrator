"""
Deterministic Intelligence Orchestrator - Execution Transcript

This module implements the execution transcript system for cryptographic traceability.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import hashlib
import json
from datetime import datetime, timezone
from enum import Enum


class EntryType(Enum):
    """Types of entries in an execution transcript."""
    SUBMISSION = "submission"
    NODE_START = "node_start"
    NODE_COMPLETE = "node_complete"
    NODE_FAILURE = "node_failure"
    FAILURE = "failure"
    COMPLETION = "completion"
    POLICY_VIOLATION = "policy_violation"


@dataclass
class TranscriptEntry:
    """A single entry in an execution transcript."""
    entry_type: EntryType
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None  # For cryptographic signing


@dataclass
class PolicyViolationEntry:
    """Structured entry for policy violations."""
    type: str = "policy_violation"
    timestamp: str
    policy_id: str
    policy_type: str
    message: str
    details: Dict[str, Any]
    signature: Optional[str] = None


@dataclass
class ExecutionTranscript:
    """
    A complete, append-only, cryptographically verifiable record of an execution.
    
    This transcript captures all aspects of an intelligence run for auditability,
    replayability, and policy enforcement verification.
    """
    
    execution_id: str
    graph_hash: str
    timestamp: datetime
    entries: List[TranscriptEntry] = field(default_factory=list)
    signature: Optional[str] = None  # For cryptographic signing
    determinism_hash: Optional[str] = None  # Hash of determinism state
    
    def add_entry(self, entry: Union[TranscriptEntry, Dict]) -> None:
        """Add an entry to the transcript."""
        if isinstance(entry, dict):
            # Convert dictionary to TranscriptEntry for consistency
            timestamp = datetime.now(timezone.utc)  # Default timestamp
            if "timestamp" in entry:
                try:
                    timestamp = datetime.fromisoformat(entry["timestamp"])
                except (ValueError, TypeError):
                    pass  # Keep default timestamp
            
            self.entries.append(TranscriptEntry(
                entry_type=EntryType(entry["type"]),
                timestamp=timestamp,
                data=entry.get("data", {}),
                signature=entry.get("signature")
            ))
        else:
            self.entries.append(entry)
    
    def verify_integrity(self) -> bool:
        """
        Verify that the transcript has not been tampered with.
        
        Returns True if integrity is maintained, False otherwise.
        """
        # In a production implementation, this would check cryptographic signatures
        # For now, we just ensure chronological ordering and valid entry types
        
        if not self.entries:
            return True
            
        # Check chronological order
        timestamps = [entry.timestamp for entry in self.entries]
        if timestamps != sorted(timestamps):
            return False
            
        # Check that all entries have valid types
        for entry in self.entries:
            if not isinstance(entry.entry_type, EntryType):
                return False
                
        return True
    
    def get_entries_by_type(self, entry_type: EntryType) -> List[TranscriptEntry]:
        """Get all entries of a specific type."""
        return [entry for entry in self.entries if entry.entry_type == entry_type]
    
    def get_node_entries(self, node_id: str) -> List[TranscriptEntry]:
        """Get all entries related to a specific node."""
        return [
            entry for entry in self.entries 
            if entry.data.get("node_id") == node_id
        ]
    
    def hash(self) -> str:
        """
        Compute a cryptographic hash of the entire transcript.
        
        This hash can be used to verify integrity and enable replay verification.
        """
        # Create a deterministic representation of all entries
        entries_data = []
        for entry in self.entries:
            entry_dict = {
                "type": entry.entry_type.value,
                "timestamp": entry.timestamp.isoformat(),
                "data": entry.data,
                "signature": entry.signature
            }
            entries_data.append(entry_dict)
        
        transcript_dict = {
            "execution_id": self.execution_id,
            "graph_hash": self.graph_hash,
            "timestamp": self.timestamp.isoformat(),
            "entries": entries_data,
            "signature": self.signature,
            "determinism_hash": self.determinism_hash
        }
        
        # Serialize and hash using canonical JSON
        serialized = json.dumps(transcript_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def sign(self, signing_key: bytes) -> None:
        """
        Sign the transcript with HMAC-SHA256.
        
        This provides cryptographic proof of authenticity and integrity.
        """
        transcript_hash = self.hash()
        import hmac
        self.signature = hmac.new(
            signing_key,
            transcript_hash.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, signing_key: bytes) -> bool:
        """
        Verify the transcript signature.
        
        Returns True if signature is valid, False otherwise.
        """
        if not self.signature:
            return False
        
        transcript_hash = self.hash()
        import hmac
        expected_signature = hmac.new(
            signing_key,
            transcript_hash.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(self.signature, expected_signature)