"""
Deterministic Intelligence Orchestrator - Core Engine

This module implements the main execution engine for deterministic intelligence orchestration.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from collections import deque, OrderedDict
import threading
import logging

from .policy import PolicyEngine, PolicyViolationError
from .graph import ExecutionGraph, GraphNode, NodeType
from .transcript import ExecutionTranscript, TranscriptEntry, EntryType
from .determinism import DeterminismTracker


logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of an execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class ExecutionContext:
    """Context for a single execution."""
    execution_id: str
    graph: ExecutionGraph
    policy_engine: PolicyEngine
    transcript: ExecutionTranscript
    determinism_tracker: DeterminismTracker
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[str] = None


class IntelligenceOrchestrator:
    """
    Main orchestrator for deterministic intelligence execution.
    
    This engine governs execution of intelligence workflows with explicit determinism,
    policy enforcement, and cryptographic traceability.
    """
    
    def __init__(self, policy_engine: PolicyEngine, max_cached_executions: int = 1000):
        self.policy_engine = policy_engine
        self._executions: OrderedDict[str, ExecutionContext] = OrderedDict()
        self._max_cached_executions = max_cached_executions
        self._lock = threading.RLock()

    def submit_graph(self, graph: ExecutionGraph) -> str:
        """
        Submit an execution graph for processing.
        
        Validates the graph and creates a new execution context.
        Returns the execution ID for tracking.
        """
        logger.info("Submitting execution graph", extra={
            "graph_hash": graph.hash(),
            "node_count": len(graph.nodes)
        })
        
        # Validate graph structure
        if not graph.validate():
            raise ValueError("Invalid execution graph")
            
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        
        # Create transcript
        transcript = ExecutionTranscript(
            execution_id=execution_id,
            graph_hash=graph.hash(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Initialize determinism tracker
        determinism_tracker = DeterminismTracker()
        
        # Create context
        context = ExecutionContext(
            execution_id=execution_id,
            graph=graph,
            policy_engine=self.policy_engine,
            transcript=transcript,
            determinism_tracker=determinism_tracker
        )
        
        with self._lock:
            self._executions[execution_id] = context
            self._cleanup_old_executions()
        
        # Record submission in transcript
        transcript.add_entry(TranscriptEntry(
            entry_type=EntryType.SUBMISSION,
            timestamp=datetime.now(timezone.utc),
            data={"graph_hash": graph.hash()}
        ))
        
        logger.info("Graph submitted successfully", extra={
            "execution_id": execution_id
        })
        return execution_id

    def execute(self, execution_id: str) -> ExecutionTranscript:
        """
        Execute a submitted execution graph.
        
        Enforces policies, executes nodes deterministically, and produces transcript.
        """
        context = None
        try:
            with self._lock:
                context = self._executions.get(execution_id)
                if not context:
                    raise ValueError(f"Unknown execution ID: {execution_id}")
                    
                if context.status != ExecutionStatus.PENDING:
                    raise RuntimeError(f"Cannot execute already-started execution: {execution_id}")
                    
                # Mark as running
                context.status = ExecutionStatus.RUNNING
            
            logger.info("Starting execution", extra={
                "execution_id": execution_id
            })
            
            # Enforce policies on entire graph
            self.policy_engine.enforce_graph_policies(context.graph, context.transcript)
            
            # Execute nodes in topological order
            self._execute_nodes_topologically(context)
                
            # Mark as completed
            with self._lock:
                context.status = ExecutionStatus.COMPLETED
            
        except Exception as e:
            if context:  # Check context exists
                with self._lock:
                    context.status = ExecutionStatus.FAILED
                    context.error = str(e)
                    
                    # Record failure in transcript
                    context.transcript.add_entry(TranscriptEntry(
                        entry_type=EntryType.FAILURE,
                        timestamp=datetime.now(timezone.utc),
                        data={"error": str(e)}
                    ))
                    
                    logger.error("Execution failed", extra={
                        "execution_id": execution_id,
                        "error": str(e)
                    }, exc_info=True)
                raise
            else:
                # Context was None, re-raise original exception
                raise
            
        finally:
            if context:  # Check context exists
                with self._lock:
                    # Record completion in transcript
                    context.transcript.add_entry(TranscriptEntry(
                        entry_type=EntryType.COMPLETION,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "status": context.status.value,
                            "duration_seconds": (datetime.now(timezone.utc) - context.start_time).total_seconds()
                        }
                    ))
                    
                    # Persist determinism hash after successful execution
                    if context.status == ExecutionStatus.COMPLETED:
                        context.transcript.determinism_hash = context.determinism_tracker.hash()
                        
                    logger.info("Execution completed", extra={
                        "execution_id": execution_id,
                        "status": context.status.value,
                        "duration_seconds": (datetime.now(timezone.utc) - context.start_time).total_seconds()
                    })
            
        return context.transcript

    def _execute_nodes_topologically(self, context: ExecutionContext) -> None:
        """Execute nodes in topological order based on dependencies."""
        # Build dependency graph
        in_degree = {node.id: 0 for node in context.graph.nodes}
        adjacency_list = {node.id: [] for node in context.graph.nodes}
        
        # Calculate in-degrees and build adjacency list
        for node in context.graph.nodes:
            for dep_id in node.dependencies:
                if dep_id in in_degree:
                    in_degree[node.id] += 1
                    adjacency_list[dep_id].append(node.id)
        
        # Initialize queue with nodes having no dependencies
        queue = deque([node.id for node in context.graph.nodes if in_degree[node.id] == 0])
        executed_nodes = set()
        
        # Process nodes in topological order
        while queue:
            current_node_id = queue.popleft()
            executed_nodes.add(current_node_id)
            
            # Find the actual node object
            current_node = next((n for n in context.graph.nodes if n.id == current_node_id), None)
            if not current_node:
                raise RuntimeError(f"Node {current_node_id} not found in graph")
                
            self._execute_node(context, current_node)
            
            # Update dependencies for neighbors
            for neighbor_id in adjacency_list[current_node_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
        
        # Check if all nodes were executed (no cycles)
        if len(executed_nodes) != len(context.graph.nodes):
            raise RuntimeError("Graph contains circular dependencies")

    def _execute_node(self, context: ExecutionContext, node: GraphNode) -> None:
        """Execute a single node with policy enforcement and determinism tracking."""
        
        # Record node start
        context.transcript.add_entry(TranscriptEntry(
            entry_type=EntryType.NODE_START,
            timestamp=datetime.now(timezone.utc),
            data={
                "node_id": node.id,
                "node_type": node.type.value,
                "node_data": node.data
            }
        ))
        
        try:
            # Enforce policy for this specific node
            self.policy_engine.enforce_node_policies(node, context.transcript)
            
            # Track determinism characteristics
            if node.determinism == "deterministic":
                context.determinism_tracker.record_deterministic_node(node.id)
            elif node.determinism == "bounded_nondeterministic":
                context.determinism_tracker.record_bounded_nondeterministic_node(node.id)
            elif node.determinism == "external_nondeterministic":
                context.determinism_tracker.record_external_nondeterministic_node(node.id)
            
            # Simulate execution (in real implementation, this would call models/tools)
            result = self._simulate_execution(node)
            
            # Record successful completion
            context.transcript.add_entry(TranscriptEntry(
                entry_type=EntryType.NODE_COMPLETE,
                timestamp=datetime.now(timezone.utc),
                data={
                    "node_id": node.id,
                    "result": result,
                    "determinism": node.determinism
                }
            ))
            
        except Exception as e:
            # Record failure
            context.transcript.add_entry(TranscriptEntry(
                entry_type=EntryType.NODE_FAILURE,
                timestamp=datetime.now(timezone.utc),
                data={
                    "node_id": node.id,
                    "error": str(e),
                    "determinism": node.determinism
                }
            ))
            
            # Re-raise to be handled by caller
            raise

    def _simulate_execution(self, node: GraphNode) -> Dict[str, Any]:
        """Simulate execution of a node (placeholder for real implementation)."""
        return {
            "node_id": node.id,
            "timestamp": time.time(),
            "result": f"Simulated result for {node.type.value}",
            "input_hash": hashlib.sha256(str(node.data).encode()).hexdigest()
        }

    def replay_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Replay an execution with deterministic guarantees.
        
        Returns verification results comparing original and replay.
        """
        context = self._executions.get(execution_id)
        if not context:
            raise ValueError(f"Unknown execution ID: {execution_id}")
            
        if context.status != ExecutionStatus.COMPLETED:
            raise ValueError(f"Can only replay completed executions")
    
        # Create a new transcript for replay
        replay_transcript = ExecutionTranscript(
            execution_id=f"{execution_id}_replay",
            graph_hash=context.graph.hash(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Get original node results for comparison
        original_results = {}
        for entry in context.transcript.get_entries_by_type(EntryType.NODE_COMPLETE):
            node_id = entry.data.get("node_id")
            if node_id:
                original_results[node_id] = entry.data.get("result")
        
        # Replay each node and compare
        mismatches = []
        for node in context.graph.nodes:
            try:
                result = self._simulate_execution(node)
                
                # For deterministic nodes, verify exact match
                if node.determinism == "deterministic":
                    original = original_results.get(node.id)
                    if original and original.get("input_hash") != result.get("input_hash"):
                        mismatches.append({
                            "node_id": node.id,
                            "reason": "Deterministic node produced different result"
                        })
                
                replay_transcript.add_entry(TranscriptEntry(
                    entry_type=EntryType.NODE_COMPLETE,
                    timestamp=datetime.now(timezone.utc),
                    data={
                        "node_id": node.id,
                        "result": result,
                        "determinism": node.determinism
                    }
                ))
            except Exception as e:
                mismatches.append({
                    "node_id": node.id,
                    "reason": f"Replay failed: {str(e)}"
                })
        
        return {
            "replay_transcript": replay_transcript,
            "verified": len(mismatches) == 0,
            "mismatches": mismatches
        }

    def verify_execution(self, execution_id: str) -> bool:
        """
        Verify that an execution is tamper-evident and reproducible.
        
        Returns True if the execution can be verified as authentic and deterministic.
        """
        context = self._executions.get(execution_id)
        if not context:
            return False
            
        # Check transcript integrity
        if not context.transcript.verify_integrity():
            return False
            
        # Verify graph hash matches
        if context.graph.hash() != context.transcript.graph_hash:
            return False
            
        # Verify determinism hash matches (if present)
        if context.transcript.determinism_hash:
            expected_determinism_hash = context.determinism_tracker.hash()
            if expected_determinism_hash != context.transcript.determinism_hash:
                return False
                
        return True

    def _cleanup_old_executions(self) -> None:
        """Remove oldest COMPLETED or FAILED executions if cache is full."""
        while len(self._executions) > self._max_cached_executions:
            # Find oldest non-active execution
            for exec_id, context in list(self._executions.items()):
                if context.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
                    del self._executions[exec_id]
                    break
            else:
                # All executions are active - cannot cleanup
                logger.warning(
                    "Cannot cleanup executions: all are active",
                    extra={"active_count": len(self._executions)}
                )
                break