"""
Deterministic Intelligence Orchestrator - Execution Graph

This module defines the execution graph model for intelligence workflows.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import hashlib
import json
from enum import Enum


class NodeType(Enum):
    """Types of nodes in an execution graph."""
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    RETRY = "retry"
    SIDE_EFFECT = "side_effect"
    OUTPUT = "output"


@dataclass
class GraphNode:
    """A single node in an execution graph."""
    id: str
    type: NodeType
    data: Dict[str, Any]
    determinism: str  # "deterministic", "bounded_nondeterministic", "external_nondeterministic"
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate node after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Node ID cannot be empty")
        if self.determinism not in ["deterministic", "bounded_nondeterministic", "external_nondeterministic"]:
            raise ValueError(f"Invalid determinism value: {self.determinism}")


@dataclass
class ExecutionGraph:
    """An immutable execution graph describing an intelligence workflow."""
    
    nodes: List[GraphNode]
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    
    def __post_init__(self) -> None:
        """Validate graph after initialization."""
        if not self.nodes:
            raise ValueError("Graph must contain at least one node")
        
        # Check for duplicate IDs
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Graph contains duplicate node IDs")
    
    def hash(self) -> str:
        """
        Compute a cryptographic hash of the entire graph.
        
        This ensures that any change to the graph results in a different hash,
        enabling tamper-evident verification.
        """
        # Create a deterministic representation
        graph_dict = {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type.value,
                    "data": node.data,
                    "determinism": node.determinism,
                    "dependencies": node.dependencies,
                    "metadata": node.metadata
                }
                for node in self.nodes
            ],
            "metadata": self.metadata,
            "version": self.version
        }
        
        # Serialize and hash using canonical JSON
        serialized = json.dumps(graph_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode()).hexdigest()
        
    def validate(self) -> bool:
        """
        Validate the execution graph structure.
        
        Returns True if valid, False otherwise.
        """
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
                
            visited.add(node_id)
            rec_stack.add(node_id)
            
            # Check dependencies
            node = next((n for n in self.nodes if n.id == node_id), None)
            if not node:
                return False
                
            for dep_id in node.dependencies:
                if has_cycle(dep_id):
                    return True
                    
            rec_stack.remove(node_id)
            return False
            
        # Check all nodes
        for node in self.nodes:
            if node.id not in visited and has_cycle(node.id):
                return False
                
        # Check for missing dependencies
        node_id_set = set([node.id for node in self.nodes])
        for node in self.nodes:
            for dep_id in node.dependencies:
                if dep_id not in node_id_set:
                    return False
                    
        return True
        
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return next((node for node in self.nodes if node.id == node_id), None)
        
    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes if node.type == node_type]