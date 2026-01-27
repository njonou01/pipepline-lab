#!/bin/bash

PID_FILE="$(dirname "$0")/.pids"

if [ ! -f "$PID_FILE" ]; then
    echo "Erreur: Aucun collector en cours (.pids non trouvé)"
    exit 1
fi

case "$1" in
    debug|DEBUG)
        echo "Passage en DEBUG..."
        while read pid; do
            kill -SIGUSR1 "$pid" 2>/dev/null && echo "  PID $pid → DEBUG"
        done < "$PID_FILE"
        ;;
    info|INFO)
        echo "Passage en INFO..."
        while read pid; do
            kill -SIGUSR2 "$pid" 2>/dev/null && echo "  PID $pid → INFO"
        done < "$PID_FILE"
        ;;
    *)
        echo "Usage: $0 [debug|info]"
        echo ""
        echo "  debug  - Afficher tous les détails"
        echo "  info   - Afficher seulement les résumés"
        exit 1
        ;;
esac

echo "Fait!"
