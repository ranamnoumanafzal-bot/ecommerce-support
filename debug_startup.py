import traceback
import sys
import os

# Add the current directory to sys.path so we can import from backend
sys.path.append(os.getcwd())

print("Testing imports and starting server...")
try:
    from backend.main import app
    import uvicorn
    print("Imports successful, starting uvicorn...")
    uvicorn.run(app, host="127.0.0.1", port=8001) # Try a different port to avoid conflicts
except Exception:
    print("FAILED with traceback:")
    traceback.print_exc()
