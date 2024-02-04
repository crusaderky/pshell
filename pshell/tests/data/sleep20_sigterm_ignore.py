"""Simple script that executes for 20s and ignores SIGTERM.
"""
import os
import signal
import time


def _handler(signum, _frame):
    """Print the incoming signal, then do nothing."""
    print(f"Receive signal {signum}")


def main():
    """Register signal handler then sleep 1s for 20 times."""
    pid = os.getpid()
    signal.signal(signal.SIGTERM, _handler)

    for i in range(1, 20 + 1):
        time.sleep(1)
        print(f"{pid}: count {i}")


if __name__ == "__main__":
    main()
