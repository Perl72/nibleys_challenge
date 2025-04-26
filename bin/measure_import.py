import time
import tracemalloc
import importlib
import sys

def measure_import(label, code_str):
    print(f"\n=== Measuring: {label} ===")
    
    # Drop any existing reference
    if 'datetime' in sys.modules:
        del sys.modules['datetime']
    
    tracemalloc.start()
    start_time = time.perf_counter()
    exec(code_str, globals())
    duration = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"Time: {duration * 1000:.4f} ms")
    print(f"Memory: Current = {current / 1024:.2f} KB, Peak = {peak / 1024:.2f} KB")


# Test: Full module import
measure_import("import datetime", "import datetime")

# Test: Selective class import
measure_import("from datetime import datetime", "from datetime import datetime")
