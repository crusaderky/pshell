"""Simple script that executes for 20s, and gracefully shuts down in 5s once
SIGTERM is received.
"""

import signal
import sys
import time


def _handler(_signum, _frame):
    """Sleep for 5s, then gracefully exit."""
    time.sleep(5)
    sys.exit(0)


def main():
    """Register signal handler then sleep 1s for 20 times."""
    signal.signal(signal.SIGTERM, _handler)
    print("ready", flush=True)
    for _ in range(1, 20 + 1):
        time.sleep(1)


if __name__ == "__main__":
    main()
