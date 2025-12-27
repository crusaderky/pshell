"""Simple script that executes for 20s and ignores SIGTERM."""

import signal
import time


def _handler(_signum, _frame):
    """Do nothing"""


def main():
    """Register signal handler then sleep 1s for 20 times."""
    signal.signal(signal.SIGTERM, _handler)
    print("ready", flush=True)
    for _ in range(1, 20 + 1):
        time.sleep(1)


if __name__ == "__main__":
    main()
