#!/usr/bin/env python3
# Tech Pulse - Lancer tous les collectors | Équipe: UCCNT

import os
import subprocess
import sys
import signal
import logging
import logger as _

logger = logging.getLogger("runner")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(SCRIPT_DIR, ".pids")
COLLECTORS = ["collector_hackernews.py", "collector_stackoverflow.py", "collector_rss.py",
              "collector_bluesky.py", "collector_nostr.py"]
processes = []


def save_pids():
    """Sauvegarder les PIDs pour changement de log à chaud"""
    with open(PID_FILE, "w") as f:
        for p in processes:
            f.write(f"{p.pid}\n")


def signal_handler(sig, frame):
    logger.warning("Arrêt de tous les collectors...")
    for p in processes:
        p.terminate()
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)


def propagate_signal(sig, frame):
    """Propager le signal aux enfants (changement log à chaud)"""
    for p in processes:
        try:
            os.kill(p.pid, sig)
        except:
            pass


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Propager SIGUSR1/SIGUSR2 aux enfants
    try:
        signal.signal(signal.SIGUSR1, propagate_signal)
        signal.signal(signal.SIGUSR2, propagate_signal)
    except AttributeError:
        pass

    logger.info("=== Démarrage de tous les collectors ===")
    for collector in COLLECTORS:
        p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, collector)], cwd=SCRIPT_DIR)
        processes.append(p)
        logger.info(f"[PID {p.pid}] {collector}")

    save_pids()
    logger.info(f"PIDs sauvegardés dans {PID_FILE}")
    logger.info("Changer log: kill -SIGUSR1 <pid> (DEBUG) | kill -SIGUSR2 <pid> (INFO)")

    for p in processes:
        p.wait()


if __name__ == "__main__":
    main()
