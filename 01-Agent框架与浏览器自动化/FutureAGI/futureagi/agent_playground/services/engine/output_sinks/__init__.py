"""
Output Sinks for Graph Execution Engine.

This package contains implementations of BaseOutputSink for different storage targets.
Sinks self-register on module import.

Current sinks:
    - cell: CellOutputSink — writes node outputs to model_hub.Cell

Adding a new sink:
    1. Create a new file (e.g., my_sink.py)
    2. Subclass BaseOutputSink and implement the store() method
    3. Self-register at the bottom: register_sink("my_sink", MySink())
    4. Import the module here to trigger registration
"""

# Import sink modules to trigger self-registration.
# Add new sinks here as they are created.
import agent_playground.services.engine.output_sinks.cell_sink  # noqa: F401
