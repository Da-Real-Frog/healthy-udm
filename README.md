# udm-ssh-toolkit

Two small shell scripts for a **UniFi Dream Machine** (UDM / UniFi OS) that work over plain SSH with your key, so there's no UniFi login, API token or MFA prompt.

| Script | What it does | Changes anything? |
|---|---|---|
| [`scripts/collect-remote.sh`](scripts/collect-remote.sh) | Takes a full read-only snapshot of the gateway and the UniFi Network database, with secrets redacted | No |
| [`scripts/forget-stale-clients.sh`](scripts/forget-stale-clients.sh) | "Forgets" clients the controller hasn't seen for N days, to clean up the client list | Only with `APPLY=1` |

Both scripts run **on the UDM** but are piped in from your own machine, so nothing needs to be copied to the device:

```sh
ssh root@unifi 'sh -s'   < scripts/collect-remote.sh > udm.txt 2> udm.stderr.txt
ssh root@unifi 'bash -s' < scripts/forget-stale-clients.sh          # dry run
```

Here `unifi` is whatever hostname or IP reaches your UDM over SSH.

## Requirements

- SSH enabled on the console (UniFi OS → Console Settings → SSH), with key-based login for `root`.
- The UniFi Network app's local MongoDB, which is on port 27117 by default, and a `mongo` or `mongosh` shell on the device. The scripts detect which one is present.
- Tested on a **UDM running UniFi OS 5.1.33 with UniFi Network 10.6.106**. Other UniFi OS consoles (UDM Pro, UDM SE, UDR, UCG) use the same layout and should work, but haven't been tested.

## Documentation

- [docs/collect-remote.md](docs/collect-remote.md): what's collected, the output format, redaction, and how to check for leaks.
- [docs/forget-stale-clients.md](docs/forget-stale-clients.md): how the cleanup decides, the dry run, backup and restore.

## Caveats

- `forget-stale-clients.sh` edits the Network app's database directly and then restarts the app. Ubiquiti doesn't support this. Routing and Wi-Fi keep working, but the UniFi UI is down for 1–2 minutes. **Take a backup first.**
- `collect-remote.sh` redacts secrets by field name. Always skim the output (see the docs) before you share it.

## Previous project

This repository used to hold *healthy-udm*, a Python monitor for zombie processes on the UDM. Recent UniFi OS releases fixed that problem, so it was retired. The old code is kept at the [`legacy-zombie-monitor`](https://github.com/Da-Real-Frog/healthy-udm/tree/legacy-zombie-monitor) tag.

## License

[MIT](LICENSE)
