# forget-stale-clients.sh

Cleans the UniFi Network client list by forgetting clients that haven't been seen for a while. That gets rid of old phones, guests' laptops, devices from a previous subnet, and names of access points you've retired. It does the same thing as selecting clients in the UI and choosing **Forget**, but in bulk, over SSH, with no UniFi login.

## Usage

```sh
# 1. Dry run: lists what would be forgotten and changes nothing
ssh root@unifi 'bash -s' < scripts/forget-stale-clients.sh

# 2. Apply, keeping a log (it includes a JSON backup of every removed entry)
ssh root@unifi 'APPLY=1 bash -s' < scripts/forget-stale-clients.sh | tee forget-$(date +%F).log

# Use a different cutoff (default 30 days)
ssh root@unifi 'DAYS=90 APPLY=1 bash -s' < scripts/forget-stale-clients.sh
```

## What it selects

A client is forgotten only if **all** of these are true:

- `last_seen` is more than `DAYS` days ago;
- it has no fixed-IP reservation (`use_fixedip`);
- it has no local DNS record (`local_dns_record_enabled`).

The dry run prints each match as `last-seen-date  MAC  last-IP  name`, plus a total. Read it. Devices that are still in use but have been offline for a while, such as a robot vacuum or a sensor, will show up there too. Give those a fixed IP, or raise `DAYS`, if you want to keep them.

## What APPLY=1 does

1. It prints every matching document as one line of JSON. This is your backup, so keep the log.
2. It runs `db.user.deleteMany(...)` with the same filter.
3. It runs `systemctl restart unifi`, so the Network app reloads and doesn't write the old entries back from memory. Routing, firewall and Wi-Fi keep working. Only the UniFi UI and controller are unavailable for 1–2 minutes.
4. It prints the new client count.

A forgotten device that comes back just shows up again as a new client. You'll only lose its friendly name and history.

## Restoring an entry

Each line under `== Backup of entries being removed ==` in your log is one client document. To put one back, on the UDM:

```sh
mongo --quiet --port 27117 ace --eval 'db.user.insertOne(<paste JSON line here>)'
systemctl restart unifi
```

If it's a lot of clients, restoring your last `.unf` backup from the UI is simpler.

## Safety notes

- This edits the controller database directly, which Ubiquiti doesn't support. Download a backup first (in the UI, look under the console's Backups settings).
- The script never touches devices (APs, switches), networks, WLANs or firewall settings. It only touches the `user` (client) collection.
