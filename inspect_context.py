"""
Root-level wrapper for tools/inspect_context.py
Usage:
    python inspect_context.py "minimum CRR for finance"
    python inspect_context.py "SLR 2082" --full
"""
import os
import sys

# Prevent network calls/hangs in HuggingFace & PyTorch
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.inspect_context import inspect_query

if __name__ == "__main__":
    args = sys.argv[1:]
    show_full = "--full" in args
    filtered_args = [a for a in args if a != "--full"]
    if filtered_args:
        inspect_query(" ".join(filtered_args), show_full=show_full)
    else:
        print("Usage: python inspect_context.py <your question> [--full]")
