#!/bin/bash
# "Forget" stale clients in the UniFi Network app (cleans old entries out of the client list),
# using only your SSH key — no UniFi login.
#
# Dry run (lists what would be forgotten, changes nothing):
#   ssh root@unifi 'bash -s' < forget-stale-clients.sh
# Apply, saving a backup of the removed entries on your Mac:
#   ssh root@unifi 'APPLY=1 bash -s' < forget-stale-clients.sh | tee forget-stale-clients-$(date +%F).log
# Change the cutoff (default 30 days):  ... 'DAYS=60 APPLY=1 bash -s' ...
#
# Skips anything with a fixed-IP reservation or a local DNS record. A forgotten device that comes back
# simply reappears as a new client (you may need to rename it). Restarts the Network app afterwards so
# it doesn't keep the old entries in memory; routing and Wi-Fi keep running.
set -uo pipefail

DAYS="${DAYS:-30}"
MONGO=$(command -v mongo || command -v mongosh) || { echo "No mongo shell found on the UDM."; exit 1; }
FILTER="{last_seen:{\$lt: Math.floor(Date.now()/1000) - $DAYS*86400}, use_fixedip:{\$ne:true}, local_dns_record_enabled:{\$ne:true}}"
q() { "$MONGO" --quiet --port 27117 ace --eval "$1"; }

echo "== Clients not seen in $DAYS+ days (excluding fixed-IP / DNS-record clients) =="
q "db.user.find($FILTER).sort({last_seen:1}).forEach(function(u){
  print(new Date(u.last_seen*1000).toISOString().slice(0,10) + '  ' + u.mac + '  ' + (u.last_ip||'-') + '  ' + (u.name||u.hostname||'(no name)'));
}); print('Total: ' + db.user.count($FILTER));"

if [ "${APPLY:-}" != 1 ]; then echo; echo "Dry run only. Re-run with APPLY=1 to forget these."; exit 0; fi

echo; echo "== Backup of entries being removed (JSON, one per line) =="
q "db.user.find($FILTER).forEach(function(u){ print(JSON.stringify(u)); })"

echo; echo "== Forgetting =="
q "printjson(db.user.deleteMany($FILTER))"

echo "== Restarting the UniFi Network app =="
systemctl restart unifi || { echo "Could not restart 'unifi'; restart the Network app from the UI."; exit 1; }
for i in $(seq 1 36); do sleep 5; q "db.user.count()" >/dev/null 2>&1 && break; done
echo "== Clients now known to the controller: $(q 'db.user.count()') =="
