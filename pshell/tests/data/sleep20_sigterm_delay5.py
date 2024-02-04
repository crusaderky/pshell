"""Simple script that executes for 20s, and gracefully shuts down in 5s once
SIGTERM is received.
"""
import os
import signal
import sys
import time


def _handler(signum, _frame):
    """Print the incoming signal, sleep for 5s then gracefully exit."""
    print(f"Receive signal {signum}")
    time.sleep(5)
    sys.exit(0)


def main():
    """Register signal handler then sleep 1s for 20 times."""
    pid = os.getpid()
    signal.signal(signal.SIGTERM, _handler)

    for i in range(1, 20 + 1):
        time.sleep(1)
        print(f"{pid}: count {i}")


if __name__ == "__main__":
    main()
