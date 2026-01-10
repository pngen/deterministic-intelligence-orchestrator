# Deterministic Intelligence Orchestrator (DIO)

## One-sentence value proposition

A production-grade control plane for deterministic, auditable, and policy-bounded intelligence execution.

## Overview

The Deterministic Intelligence Orchestrator (DIO) is a control plane designed to govern the execution of artificial intelligence workflows in enterprise, regulatory, and safety-critical environments. Unlike workflow engines or agent frameworks, DIO focuses on ensuring that intelligence execution is:

- **Reproducible**: Every execution can be replayed with equivalent results
- **Auditable**: Complete, cryptographically verifiable records of all actions
- **Governed**: Strict policy enforcement before any execution begins
- **Deterministic**: Explicit modeling of determinism boundaries

DIO operates on **Execution Graphs**, not pipelines. An execution graph is an immutable, declarative description of an intelligence run that includes inputs, models, tool interfaces, policy constraints, allowed side effects, failure handling, determinism boundaries, and output commitments.

## Architecture diagram
<pre>
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Execution     │    │   Policy         │    │  Determinism       │
│   Graph         │───▶│   Engine         │───▶│  Tracker           │
│                 │    │                  │    │                    │
│ - Nodes         │    │ - Rules          │    │ - Node types       │
│ - Metadata      │    │ - Enforcement    │    │ - Determinism      │
│ - Hash          │    │ - Violations     │    │   tracking         │
└─────────────────┘    └──────────────────┘    └────────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│  Execution      │    │  Execution       │    │  Execution         │
│  Engine         │───▶│  Transcript      │───▶│  Replay            │
│                 │    │                  │    │                    │
│ - Graph         │    │ - Entries        │    │ - Verification     │
│ - Policy        │    │ - Integrity      │    │ - Replay           │
│ - Execution     │    │ - Hashing        │    │ - Validation       │
│   tracking      │    │ - Signing        │    │                    │
└─────────────────┘    └──────────────────┘    └────────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Adapters      │    │  Storage         │    │  External          │
│                 │    │                  │    │  Systems           │
│ - Data          │    │ - Graphs         │    │ - Models           │
│ - Compute       │    │ - Transcripts    │    │ - Tools            │
│ - Scheduling    │    │ - Policies       │    │ - Orchestration    │
└─────────────────┘    └──────────────────┘    └────────────────────┘
</pre>

## Core Components

### 1. Execution Graphs
Immutable, declarative descriptions of intelligence workflows that include:
- Inputs and outputs
- Model calls and tool interfaces
- Policy constraints
- Determinism boundaries
- Side effect specifications

### 2. Policy Engine
Enforces governance policies before execution:
- Model access restrictions
- Tool invocation limits
- Resource usage caps
- Data egress controls
- Retry behavior rules
- Cost ceilings
- Human approval gates

### 3. Execution Engine
Manages the lifecycle of intelligence workflows:
- Validates graphs and enforces policies
- Executes nodes deterministically in topological order
- Tracks side effects and entropy sources
- Produces cryptographically verifiable transcripts

### 4. Execution Transcript
Append-only, tamper-evident records of execution:
- Complete audit trail of all actions
- Cryptographic hashing for integrity verification
- Signed entries for authenticity
- Replayable execution logs

### 5. Determinism Tracker
Explicitly models determinism characteristics:
- Fully deterministic nodes
- Bounded nondeterministic nodes
- External nondeterministic nodes
- Hash-based verification of determinism

## Usage

```python
from dio.core import IntelligenceOrchestrator, PolicyEngine, PolicyRule, PolicyType
from dio.core.graph import ExecutionGraph, GraphNode, NodeType

# Create policy engine and add rules
policy_engine = PolicyEngine()
policy_engine.add_rule(PolicyRule(
    id="model_access",
    type=PolicyType.MODEL_ACCESS,
    conditions={"allowed_models": ["gpt-3.5"]},
    actions=["allow"],
    description="Only allow gpt-3.5 model"
))

# Create orchestrator
orchestrator = IntelligenceOrchestrator(policy_engine)

# Define execution graph
node1 = GraphNode(
    id="model_call_1",
    type=NodeType.MODEL_CALL,
    data={"model_name": "gpt-3.5"},
    determinism="deterministic"
)

graph = ExecutionGraph(nodes=[node1])

# Submit and execute
execution_id = orchestrator.submit_graph(graph)
transcript = orchestrator.execute(execution_id)

# Verify execution
is_valid = orchestrator.verify_execution(execution_id)
```

## Design Principles
1. **Determinism First**
All execution behavior must be explicitly modeled and documented. No implicit assumptions about model determinism.

2. **Governance Over Optimization**
Policy enforcement happens before execution, not after. All decisions are auditable and defensible.

3. **Cryptographic Integrity**
Every component is designed with cryptographic verification in mind - from graphs to transcripts to execution logs.

4. **Explicit State Management**
No hidden global state. All execution state is explicit and traceable through the transcript system.

5. **Composability**
Each module can be replaced or extended independently without affecting core functionality.

## What DIO Is Not
DIO is not:

- A workflow engine
- An agent framework
- A model training platform
- A data movement tool
- An autonomous goal-seeking system

## Requirements
- Python 3.8+
- Strong typing throughout
- Comprehensive unit tests
- Immutable data structures where appropriate
- Explicit error handling with clear failure messages
- Cryptographically secure hashing (SHA-256)
- Deterministic execution semantics
- Policy-driven governance model

## Security Considerations

DIO implements cryptographic guarantees including:
- Execution graph hashing
- Transcript hashing
- Optional signing of runs
- Tamper-evident logs
- Replay verification
- Policy validation before execution

The system uses established cryptographic primitives to ensure correctness and traceability over novelty.

## Logging Configuration
DIO uses Python's standard logging library. Configure logging in your application:

```python
import logging

# Basic configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# For structured logging (recommended for production)
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'dio': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## Installation
Install DIO using pip:
```bash
pip install dio
```

Or install from source:
```bash
git clone https://github.com/yourorg/dio.git
cd dio
pip install -e .
```

## Development
To contribute to DIO, install the development dependencies:
```bash
pip install -e .[dev]
```

Run tests with:
```bash
pytest
```