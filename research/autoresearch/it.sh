#!/bin/zsh
# usage: MINI=user@host ./it.sh cNN   -> copies candidate files to the compute machine and runs one counted iteration there
cd "$(dirname "$0")"
: ${MINI:?set MINI to the SSH login of the compute machine}
rsync -a lib.py candidates data_cards JOURNAL.md "$MINI":coffee_project/autoresearch/ 2>/dev/null
ssh "$MINI" "cd ~/coffee_project/autoresearch && ./run.sh core.py iter candidates/$1.py 2>&1 | tail -${2:-12}"
