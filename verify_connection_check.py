
import os
import sys
import traceback

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(".env")

# Disable reasoning for faster check
os.environ["NIM_REASONING"] = "false"

from backend.core.llm_client import nim_chat

print(f"Testing DeepSeek Connection...")
print(f"API Key present: {bool(os.getenv('NIM_API_KEY'))}")
print(f"Model: {os.getenv('NIM_MODEL', 'Not set')}")

try:
    response = nim_chat("Reply with 'Success' if you can hear me.")
    if response:
        print("\nSUCCESS: Received response:")
        print(response)
    else:
        print("\nFAILURE: No response received (nim_chat returned None).")
except Exception:
    print("\nERROR occurred:")
    traceback.print_exc()
