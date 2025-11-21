import sys
import os

# Print current directory
print("Current directory:", os.getcwd())
print()

# Print __file__ location
print("Script location:", os.path.abspath(__file__))
print()

# Calculate backend path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
print("Backend path:", backend_path)
print("Backend exists?", os.path.exists(backend_path))
print()

# Check if Python files exist
files_to_check = [
    'fact_extract.py',
    'refdatabase.py',
    'confidence_scorer.py',
    'contradiction_detector.py',
    'response_formatter.py'
]

for file in files_to_check:
    full_path = os.path.join(backend_path, file)
    exists = os.path.exists(full_path)
    print(f"{file}: {'✓ EXISTS' if exists else '✗ MISSING'} ({full_path})")

print()

# Add to path
sys.path.insert(0, backend_path)
print("Python path:", sys.path[:3])

# Try importing
try:
    from fact_extract import fact_extractor
    print("\n✓ SUCCESS: fact_extractor imported!")
except Exception as e:
    print(f"\n✗ FAILED: {e}")