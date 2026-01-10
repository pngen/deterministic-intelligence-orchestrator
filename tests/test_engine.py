"""
Unit tests for the IntelligenceOrchestrator core engine.
"""

import unittest
from datetime import datetime, timezone
from dio.core.engine import IntelligenceOrchestrator, ExecutionStatus
from dio.core.policy import PolicyEngine, PolicyRule, PolicyType
from dio.core.graph import ExecutionGraph, GraphNode, NodeType
from dio.core.transcript import ExecutionTranscript


class TestIntelligenceOrchestrator(unittest.TestCase):
    
    def setUp(self):
        self.policy_engine = PolicyEngine()
        self.orchestrator = IntelligenceOrchestrator(self.policy_engine)
        
    def test_submit_graph(self):
        """Test submitting a valid execution graph."""
        # Create a simple graph
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        graph = ExecutionGraph(
            nodes=[node1],
            metadata={"description": "Test graph"}
        )
        
        # Submit the graph
        execution_id = self.orchestrator.submit_graph(graph)
        
        # Verify it was stored
        self.assertIn(execution_id, self.orchestrator._executions)
        
        # Verify transcript was created
        context = self.orchestrator._executions[execution_id]
        self.assertIsNotNone(context.transcript)
        
    def test_execute_success(self):
        """Test successful execution of a graph."""
        # Create a simple graph with two nodes
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        node2 = GraphNode(
            id="node2",
            type=NodeType.TOOL_CALL,
            data={"tool_name": "calculator"},
            determinism="deterministic"
        )
        
        graph = ExecutionGraph(
            nodes=[node1, node2],
            metadata={"description": "Test graph"}
        )
        
        # Submit the graph
        execution_id = self.orchestrator.submit_graph(graph)
        
        # Execute it
        transcript = self.orchestrator.execute(execution_id)
        
        # Verify status
        context = self.orchestrator._executions[execution_id]
        self.assertEqual(context.status, ExecutionStatus.COMPLETED)
        
        # Verify transcript was populated
        self.assertGreater(len(transcript.entries), 0)
        
        # Verify determinism hash was set
        self.assertIsNotNone(transcript.determinism_hash)
        
    def test_execute_with_policy_violation(self):
        """Test execution fails when policy is violated."""
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
        node = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        graph = ExecutionGraph(
            nodes=[node],
            metadata={"description": "Test graph"}
        )
        
        # Submit the graph
        execution_id = self.orchestrator.submit_graph(graph)
        
        # Execute it - should fail
        with self.assertRaises(Exception):
            self.orchestrator.execute(execution_id)
            
    def test_replay_execution(self):
        """Test replaying an execution."""
        # Create a simple graph
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        graph = ExecutionGraph(
            nodes=[node1],
            metadata={"description": "Test graph"}
        )
        
        # Submit and execute
        execution_id = self.orchestrator.submit_graph(graph)
        transcript = self.orchestrator.execute(execution_id)
        
        # Replay the execution
        replay_result = self.orchestrator.replay_execution(execution_id)
        
        # Verify replay was successful
        self.assertIsNotNone(replay_result["replay_transcript"])
        self.assertTrue(replay_result["verified"])
        
    def test_verify_execution(self):
        """Test verifying an execution."""
        # Create a simple graph
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        graph = ExecutionGraph(
            nodes=[node1],
            metadata={"description": "Test graph"}
        )
        
        # Submit and execute
        execution_id = self.orchestrator.submit_graph(graph)
        transcript = self.orchestrator.execute(execution_id)
        
        # Verify the execution
        is_valid = self.orchestrator.verify_execution(execution_id)
        self.assertTrue(is_valid)
        
    def test_execute_nodes_topologically(self):
        """Test that nodes execute in topological order."""
        # Create a graph with dependencies
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        node2 = GraphNode(
            id="node2",
            type=NodeType.TOOL_CALL,
            data={"tool_name": "calculator"},
            determinism="deterministic",
            dependencies=["node1"]
        )
        
        graph = ExecutionGraph(
            nodes=[node2, node1],
            metadata={"description": "Test graph"}
        )
        
        # Submit the graph
        execution_id = self.orchestrator.submit_graph(graph)
        
        # Execute it - should not raise dependency errors
        transcript = self.orchestrator.execute(execution_id)
        
        # Verify status
        context = self.orchestrator._executions[execution_id]
        self.assertEqual(context.status, ExecutionStatus.COMPLETED)
        
    def test_execute_with_cycle_detection(self):
        """Test that execution fails with circular dependencies."""
        # Create a graph with circular dependencies
        node1 = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic",
            dependencies=["node2"]
        )
        
        node2 = GraphNode(
            id="node2",
            type=NodeType.TOOL_CALL,
            data={"tool_name": "calculator"},
            determinism="deterministic",
            dependencies=["node1"]
        )
        
        graph = ExecutionGraph(
            nodes=[node1, node2],
            metadata={"description": "Test graph"}
        )
        
        # Submit the graph
        execution_id = self.orchestrator.submit_graph(graph)
        
        # Execute it - should fail due to cycle
        with self.assertRaises(RuntimeError):
            self.orchestrator.execute(execution_id)
            
    def test_cleanup_old_executions(self):
        """Test that old executions are cleaned up."""
        # Create orchestrator with small cache
        orchestrator = IntelligenceOrchestrator(
            self.policy_engine,
            max_cached_executions=2
        )
        
        # Submit 3 graphs
        node = GraphNode(
            id="node1",
            type=NodeType.MODEL_CALL,
            data={"model_name": "gpt-4"},
            determinism="deterministic"
        )
        
        exec_ids = []
        for i in range(3):
            graph = ExecutionGraph(
                nodes=[node],
                metadata={"description": f"Test graph {i}"}
            )
            exec_id = orchestrator.submit_graph(graph)
            orchestrator.execute(exec_id)
            exec_ids.append(exec_id)
        
        # First execution should be cleaned up
        self.assertNotIn(exec_ids[0], orchestrator._executions)
        # Last two should remain
        self.assertIn(exec_ids[1], orchestrator._executions)
        self.assertIn(exec_ids[2], orchestrator._executions)


if __name__ == '__main__':
    unittest.main()