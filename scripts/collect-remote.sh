#!/bin/sh
# Read-only inventory of a UniFi Dream Machine. Run from any machine with SSH access:
#   ssh root@unifi 'sh -s' < collect-remote.sh > udm.txt 2> udm.stderr.txt
# Writes nothing on the UDM; everything goes to stdout.
# Secrets in the UniFi database (Wi-Fi keys, passwords, tokens, x_* fields) are replaced with [REDACTED].

sec() { echo; echo "===== $1 ====="; }

sec "system"
date -u; uname -a; uptime
cat /etc/os-release 2>/dev/null
ubnt-device-info summary 2>/dev/null
dpkg -l 2>/dev/null | grep -Ei 'unifi|uos|udapi'

sec "interfaces"
ip -br addr
ip -d link

sec "bridges-vlans"
bridge link
bridge vlan show
bridge fdb show | grep -v permanent

sec "ethtool-ports"
for i in $(ls /sys/class/net | grep -E '^(eth|switch|port)'); do echo "--- $i"; ethtool "$i" 2>/dev/null | grep -E 'Speed|Duplex|Link detected'; done

sec "routes"
ip rule
ip route show table all
ip -6 route

sec "neighbors"
ip neigh

sec "dhcp-leases"
ls -la /run/ 2>/dev/null | grep -i -E 'dnsmasq|dhcp|lease'
cat /run/dnsmasq.leases /run/dnsmasq.dhcp.leases /run/dhcpd*.leases 2>/dev/null

sec "dnsmasq-config"
cat /run/dnsmasq.conf.d/*.conf 2>/dev/null | grep -viE 'secret|password|key='

sec "resolv"
cat /etc/resolv.conf

sec "firewall-iptables-v4"
iptables-save

sec "firewall-iptables-v6"
ip6tables-save

sec "firewall-nft"
nft list ruleset 2>/dev/null

sec "wireless"
iw dev 2>/dev/null

sec "mca-dump"
mca-dump 2>/dev/null | head -c 500000

sec "unifi-db"
MONGO=$(command -v mongo || command -v mongosh)
if [ -z "$MONGO" ]; then echo "no mongo shell on this UDM"; else
"$MONGO" --quiet --port 27117 ace <<'EOF'
var scrub = function (o) {
  if (o && typeof o === 'object') {
    for (var k in o) {
      if (/^x_|pass|secret|psk|private|token|key$|keys$/i.test(k)) o[k] = '[REDACTED]';
      else scrub(o[k]);
    }
  }
  return o;
};
['networkconf','wlanconf','wlangroup','device','user','usergroup','portconf',
 'firewallrule','firewallgroup','firewall_zone','firewall_policy','traffic_rule',
 'portforward','routing','dhcp_option','dynamicdns','setting','site'].forEach(function (c) {
  print('----- ' + c + ' -----');
  db.getCollection(c).find().forEach(function (d) { printjson(scrub(d)); });
});
EOF
fi

sec "autobackups (listing only)"
ls -la /data/unifi/data/backup/autobackup/ 2>/dev/null || ls -la /usr/lib/unifi/data/backup/autobackup/ 2>/dev/null

sec "done"
