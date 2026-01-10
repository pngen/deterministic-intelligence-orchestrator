"""
Deterministic Intelligence Orchestrator - Policy Engine

This module implements policy enforcement for intelligence execution governance.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import logging

from .graph import ExecutionGraph, GraphNode, NodeType
from .transcript import ExecutionTranscript, TranscriptEntry, EntryType


logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of policies that can be enforced."""
    MODEL_ACCESS = "model_access"
    TOOL_ACCESS = "tool_access"
    RESOURCE_LIMITS = "resource_limits"
    DATA_EGRESS = "data_egress"
    RETRY_BEHAVIOR = "retry_behavior"
    SIDE_EFFECTS = "side_effects"
    COST_CEILING = "cost_ceiling"
    HUMAN_APPROVAL = "human_approval"


class PolicyViolationError(Exception):
    """Raised when a policy is violated during execution."""
    def __init__(self, message: str, policy_type: PolicyType, details: Dict[str, Any]):
        self.message = message
        self.policy_type = policy_type
        self.details = details
        super().__init__(message)


@dataclass
class PolicyRule:
    """A single policy rule that can be enforced."""
    id: str
    type: PolicyType
    conditions: Dict[str, Any]
    actions: List[str]
    description: str
    
    def __post_init__(self) -> None:
        """Validate policy rule after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Policy rule ID cannot be empty")
        if not self.actions:
            raise ValueError("Policy rule must have at least one action")
        if not self.conditions:
            raise ValueError("Policy rule must have conditions")
        
        # Validate policy-specific conditions
        if self.type == PolicyType.MODEL_ACCESS:
            if "allowed_models" not in self.conditions:
                raise ValueError("MODEL_ACCESS policy requires 'allowed_models' condition")
            if not isinstance(self.conditions["allowed_models"], list):
                raise ValueError("'allowed_models' must be a list")
        elif self.type == PolicyType.TOOL_ACCESS:
            if "allowed_tools" not in self.conditions:
                raise ValueError("TOOL_ACCESS policy requires 'allowed_tools' condition")
            if not isinstance(self.conditions["allowed_tools"], list):
                raise ValueError("'allowed_tools' must be a list")


class PolicyEngine:
    """
    Policy enforcement engine for intelligence execution governance.
    
    Enforces policies before execution and records violations in transcripts.
    """
    
    def __init__(self) -> None:
        self.rules: List[PolicyRule] = []
        
    def add_rule(self, rule: PolicyRule) -> None:
        """Add a policy rule to the engine."""
        self.rules.append(rule)
        
    def enforce_graph_policies(self, graph: ExecutionGraph, transcript: ExecutionTranscript) -> None:
        """
        Enforce all policies on an entire execution graph.
        
        Raises PolicyViolationError if any policy is violated.
        """
        for rule in self.rules:
            try:
                self._enforce_rule(rule, graph, transcript)
            except PolicyViolationError as e:
                # Record violation and re-raise
                transcript.add_entry(TranscriptEntry(
                    entry_type=EntryType.POLICY_VIOLATION,
                    timestamp=datetime.now(timezone.utc),
                    data={
                        "policy_id": rule.id,
                        "policy_type": rule.type.value,
                        "message": e.message,
                        "details": e.details
                    }
                ))
                raise
                
    def enforce_node_policies(self, node: GraphNode, transcript: ExecutionTranscript) -> None:
        """
        Enforce policies on a single execution node.
        
        Raises PolicyViolationError if any policy is violated.
        """
        for rule in self.rules:
            try:
                self._enforce_rule(rule, node, transcript)
            except PolicyViolationError as e:
                # Record violation and re-raise
                transcript.add_entry(TranscriptEntry(
                    entry_type=EntryType.POLICY_VIOLATION,
                    timestamp=datetime.now(timezone.utc),
                    data={
                        "policy_id": rule.id,
                        "policy_type": rule.type.value,
                        "message": e.message,
                        "details": e.details
                    }
                ))
                raise
                
    def _enforce_rule(self, rule: PolicyRule, target: Union[ExecutionGraph, GraphNode], transcript: ExecutionTranscript) -> None:
        """Enforce a single policy rule."""
        if isinstance(target, ExecutionGraph):
            self._enforce_graph_rule(rule, target, transcript)
        elif isinstance(target, GraphNode):
            self._enforce_node_rule(rule, target, transcript)
            
    def _enforce_graph_rule(self, rule: PolicyRule, graph: ExecutionGraph, transcript: ExecutionTranscript) -> None:
        """Enforce a policy rule on an entire execution graph."""
        # This is a placeholder - specific implementations would be added based on policy type
        pass
        
    def _enforce_node_rule(self, rule: PolicyRule, node: GraphNode, transcript: ExecutionTranscript) -> None:
        """Enforce a policy rule on a single execution node."""
        if rule.type == PolicyType.MODEL_ACCESS:
            self._enforce_model_access_policy(rule, node, transcript)
        elif rule.type == PolicyType.TOOL_ACCESS:
            self._enforce_tool_access_policy(rule, node, transcript)
            
    def _enforce_model_access_policy(self, rule: PolicyRule, node: GraphNode, transcript: ExecutionTranscript) -> None:
        """Enforce model access policy."""
        if node.type != NodeType.MODEL_CALL:
            return
            
        model_name = node.data.get("model_name")
        allowed_models = rule.conditions.get("allowed_models", [])
        
        if model_name and model_name not in allowed_models:
            raise PolicyViolationError(
                f"Model '{model_name}' not allowed by policy",
                PolicyType.MODEL_ACCESS,
                {
                    "model_name": model_name,
                    "allowed_models": allowed_models,
                    "policy_id": rule.id
                }
            )
            
    def _enforce_tool_access_policy(self, rule: PolicyRule, node: GraphNode, transcript: ExecutionTranscript) -> None:
        """Enforce tool access policy."""
        if node.type != NodeType.TOOL_CALL:
            return
            
        tool_name = node.data.get("tool_name")
        allowed_tools = rule.conditions.get("allowed_tools", [])
        
        if tool_name and tool_name not in allowed_tools:
            raise PolicyViolationError(
                f"Tool '{tool_name}' not allowed by policy",
                PolicyType.TOOL_ACCESS,
                {
                    "tool_name": tool_name,
                    "allowed_tools": allowed_tools,
                    "policy_id": rule.id
                }
            )