"""
Deterministic Intelligence Orchestrator - Determinism Tracker

This module provides tracking of determinism characteristics for execution nodes.
"""

from dataclasses import dataclass, field
from typing import Set, Dict, Any, List
import hashlib


@dataclass
class DeterminismTracker:
    """Tracks determinism characteristics for execution nodes."""
    
    deterministic_nodes: Set[str] = field(default_factory=set)
    bounded_nondeterministic_nodes: Set[str] = field(default_factory=set)
    external_nondeterministic_nodes: Set[str] = field(default_factory=set)
    
    def record_deterministic_node(self, node_id: str) -> None:
        """Record a node as fully deterministic."""
        self.deterministic_nodes.add(node_id)
    
    def record_bounded_nondeterministic_node(self, node_id: str) -> None:
        """Record a node as bounded nondeterministic."""
        self.bounded_nondeterministic_nodes.add(node_id)
    
    def record_external_nondeterministic_node(self, node_id: str) -> None:
        """Record a node as external nondeterministic."""
        self.external_nondeterministic_nodes.add(node_id)
    
    def get_determinism_summary(self) -> Dict[str, List[str]]:
        """Get a summary of all determinism classifications."""
        return {
            "deterministic": sorted(list(self.deterministic_nodes)),
            "bounded_nondeterministic": sorted(list(self.bounded_nondeterministic_nodes)),
            "external_nondeterministic": sorted(list(self.external_nondeterministic_nodes))
        }
    
    def hash(self) -> str:
        """Compute a cryptographic hash of the determinism state."""
        # Create a deterministic representation
        determinism_dict = {
            "deterministic": sorted(list(self.deterministic_nodes)),
            "bounded_nondeterministic": sorted(list(self.bounded_nondeterministic_nodes)),
            "external_nondeterministic": sorted(list(self.external_nondeterministic_nodes))
        }
        
        # Serialize and hash
        import json
        serialized = json.dumps(determinism_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode()).hexdigest()