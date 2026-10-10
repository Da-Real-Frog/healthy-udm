# collect-remote.sh

A read-only inventory of a UniFi Dream Machine. It writes nothing on the device: everything goes to stdout, which you redirect into a file on your own machine.

```sh
ssh root@unifi 'sh -s' < scripts/collect-remote.sh > udm.txt 2> udm.stderr.txt
```

It takes a few seconds, and the output is typically 0.5–1 MB of text.

## What it collects

Each section starts with a `===== name =====` header.

| Section | Source | Useful for |
|---|---|---|
| `system` | `uname`, `/etc/os-release`, `ubnt-device-info`, installed UniFi packages | Model, firmware, app versions |
| `interfaces` | `ip -br addr`, `ip -d link` | Bridges per network (`br0`, `br2`…), VLAN sub-interfaces, WAN address |
| `bridges-vlans` | `bridge link`, `bridge vlan`, `bridge fdb` | Which MAC addresses were learned on which port, VLAN or radio |
| `ethtool-ports` | `ethtool` | Link speed and duplex per port |
| `routes` | `ip rule`, `ip route show table all` | Policy routing, WAN tables, IPv6 prefixes |
| `neighbors` | `ip neigh` | Which clients are live right now (ARP) |
| `dhcp-leases`, `dnsmasq-config`, `resolv` | `/run/dnsmasq*`, `/etc/resolv.conf` | DHCP and DNS |
| `firewall-iptables-v4/v6`, `firewall-nft` | `iptables-save`, `ip6tables-save`, `nft list ruleset` | The rules actually in force |
| `wireless` | `iw dev` | Radios and virtual APs |
| `mca-dump` | `mca-dump` (capped at 500 KB) | Live device state as the controller sees it |
| `unifi-db` | MongoDB `ace` database | Controller config: networks, WLANs, devices, clients, firewall zones and policies, port forwards, settings |
| `autobackups` | directory listing only | Where the `.unf` auto-backups are, and how recent they are |

Collections dumped from the database: `networkconf`, `wlanconf`, `wlangroup`, `device`, `user` (clients), `usergroup`, `portconf`, `firewallrule`, `firewallgroup`, `firewall_zone`, `firewall_policy`, `traffic_rule`, `portforward`, `routing`, `dhcp_option`, `dynamicdns`, `setting`, `site`. Each one starts with a `----- name -----` line, and documents are printed with `printjson`.

## Redaction

Before printing, each database document is walked recursively. Any field whose **name** matches

```
^x_   pass   secret   psk   private   token   key$   keys$
```

has its value replaced with `[REDACTED]`. That covers Wi-Fi passphrases (`x_passphrase`), RADIUS and VPN secrets, SSH hashes and keys, API tokens and the like. It's deliberately broad, so a few harmless fields that happen to end in `key` are redacted too.

Two things are **not** redacted: the `mca-dump` section and the plain Linux command output. They don't normally contain credentials, but they do contain your public IP, MAC addresses and hostnames.

### Check for leaks before sharing

```sh
grep -niE 'passphrase|psk|password|secret|private_key|token' udm.txt | grep -v REDACTED
```

The only lines left should be things like `"wpa_mode"`, `"wpa_enc"` and `"security" : "wpapsk"`.

## Parsing tips

- The `printjson` output isn't strict JSON, because it contains `ObjectId("…")`, `UUID("…")`, `NumberLong(…)` and `ISODate("…")`. Replace those wrappers with their inner value, then use `json.loads` on each block from `{` at column 0 to the matching `}` at column 0.
- Network, WLAN and client records link to each other through `_id` and `networkconf_id`.
- `mca-dump` can be cut off at 500 KB, because the DPI stats are large. Raise the `head -c` limit in the script if you need the whole thing.

## Known limitations

- DHCP leases on recent UniFi OS live in `/run/dnsmasq.lease`, which the current version doesn't read. Client IPs still come from `ip neigh` and the `user` collection.
- Unmanaged switches, MoCA adapters and anything else that isn't UniFi won't show up, except as MAC addresses in the bridge forwarding table.
