"""
Unit tests for the PolicyEngine.
"""

import unittest
from datetime import datetime, timezone
from dio.core.policy import PolicyEngine, PolicyRule, PolicyType, PolicyViolationError
from dio.core.graph import ExecutionGraph, GraphNode, NodeType
from dio.core.transcript import ExecutionTranscript


class TestPolicyEngine(unittest.TestCase):
    
    def setUp(self):
        self.policy_engine = PolicyEngine()
        
    def test_add_rule(self):
        """Test adding a policy rule."""
        rule = PolicyRule(
            id="test_rule",
            type=PolicyType.MODEL_ACCESS,
            conditions={"allowed_models": ["gpt-3.5"]},
            actions=["allow"],
            description="Test rule"
        )
        
        self.policy_engine.add_rule(rule)
        self.assertEqual(len(self.policy_engine.rules), 1)
        
    def test_enforce_model_access_rule(self):
        """Test enforcing model access policy."""
        # Add a restrictive policy
        rule = PolicyRule(
            id="model_access",
            type=PolicyType.MODEL_ACCESS,
            conditions={"allowed_models": ["gpt-3.5"]},
            actions=["allow"],
            description="Only allow gpt-3.5 model"
        )
        self.policy_engine.add_rule(rule)
        
        # Create a graph with an allowed model
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-3.5"},
            determinism="deterministic"
        )
        
        graph = ExecutionGraph(nodes=[node1])
        
        # Create transcript for testing
        transcript = ExecutionTranscript(
            execution_id="test",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Should not raise exception
        try:
            self.policy_engine.enforce_graph_policies(graph, transcript)
            success = True
        except PolicyViolationError:
            success = False
            
        self.assertTrue(success)
        
    def test_enforce_model_access_rule_violation(self):
        """Test policy violation with disallowed model."""
        # Add a restrictive policy
        rule = PolicyRule(
            id="model_access",
            type=PolicyType.MODEL_ACCESS,
            conditions={"allowed_models": ["gpt-3.5"]},
            actions=["allow"],
            description="Only allow gpt-3.5 model"
        )
        self.policy_engine.add_rule(rule)
        
        # Create a graph with a disallowed model
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        graph = ExecutionGraph(nodes=[node1])
        
        # Create transcript for testing
        transcript = ExecutionTranscript(
            execution_id="test",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Should raise exception
        with self.assertRaises(PolicyViolationError):
            self.policy_engine.enforce_graph_policies(graph, transcript)
            
    def test_enforce_node_policy(self):
        """Test enforcing policy on a single node."""
        # Add a restrictive policy
        rule = PolicyRule(
            id="model_access",
            type=PolicyType.MODEL_ACCESS,
            conditions={"allowed_models": ["gpt-3.5"]},
            actions=["allow"],
            description="Only allow gpt-3.5 model"
        )
        self.policy_engine.add_rule(rule)
        
        # Create a node with an allowed model
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-3.5"},
            determinism="deterministic"
        )
        
        # Create transcript for testing
        transcript = ExecutionTranscript(
            execution_id="test",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Should not raise exception
        try:
            self.policy_engine.enforce_node_policies(node1, transcript)
            success = True
        except PolicyViolationError:
            success = False
            
        self.assertTrue(success)
        
    def test_enforce_node_policy_violation(self):
        """Test policy violation on a single node."""
        # Add a restrictive policy
        rule = PolicyRule(
            id="model_access",
            type=PolicyType.MODEL_ACCESS,
            conditions={"allowed_models": ["gpt-3.5"]},
            actions=["allow"],
            description="Only allow gpt-3.5 model"
        )
        self.policy_engine.add_rule(rule)
        
        # Create a node with a disallowed model
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        # Create transcript for testing
        transcript = ExecutionTranscript(
            execution_id="test",
            graph_hash="test_hash",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Should raise exception
        with self.assertRaises(PolicyViolationError):
            self.policy_engine.enforce_node_policies(node1, transcript)
            
    def test_policy_rule_validation(self):
        """Test policy rule validation."""
        # Test empty ID
        with self.assertRaises(ValueError):
            PolicyRule(
                id="",
                type=PolicyType.MODEL_ACCESS,
                conditions={"allowed_models": ["gpt-3.5"]},
                actions=["allow"],
                description="Test rule"
            )
            
        # Test no actions
        with self.assertRaises(ValueError):
            PolicyRule(
                id="test_rule",
                type=PolicyType.MODEL_ACCESS,
                conditions={"allowed_models": ["gpt-3.5"]},
                actions=[],
                description="Test rule"
            )
            
        # Test no conditions
        with self.assertRaises(ValueError):
            PolicyRule(
                id="test_rule",
                type=PolicyType.MODEL_ACCESS,
                conditions={},
                actions=["allow"],
                description="Test rule"
            )


if __name__ == '__main__':
    unittest.main()