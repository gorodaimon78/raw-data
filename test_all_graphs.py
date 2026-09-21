import sys
import os
import importlib.util
from pathlib import Path

agents_dir = Path(__file__).parent / "agents_code"
folders = sorted([d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])

print(f"Discovered {len(folders)} agent packages.")
results = {}

for folder in folders:
    agent_file = folder / "agent.py"
    if not agent_file.exists():
        continue
    agent_id = folder.name
    print(f"Testing {agent_id}...", end=" ", flush=True)
    try:
        sys.path.insert(0, str(folder))
        module_name = f"agents_code_{agent_id}"
        spec = importlib.util.spec_from_file_location(module_name, str(agent_file))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        
        # Build graph
        if hasattr(mod, "build_graph"):
            code_args = mod.build_graph.__code__.co_varnames
            if "checkpointer" in code_args:
                from langgraph.checkpoint.memory import MemorySaver
                g = mod.build_graph(checkpointer=MemorySaver())
            else:
                g = mod.build_graph()
            
            # Verify mermaid export
            mermaid = g.get_graph().draw_mermaid()
            assert len(mermaid) > 20
            print("OK (Graph compiled successfully)")
            results[agent_id] = "OK"
        else:
            print("WARN (No build_graph found)")
            results[agent_id] = "NO_BUILD_GRAPH"
    except Exception as e:
        print(f"ERROR: {e}")
        results[agent_id] = f"ERROR: {e}"
    finally:
        if str(folder) in sys.path:
            sys.path.remove(str(folder))

print("\n--- Summary ---")
for k, v in results.items():
    print(f"  {k}: {v}")
