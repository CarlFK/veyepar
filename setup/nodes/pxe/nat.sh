#!/bin/bash -xe

iptables -A FORWARD -o wlan0 -i eth0 -s 192.168.0.0/24 -m conntrack --ctstate NEW -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A POSTROUTING -t nat -j MASQUERADE
echo 1 > /proc/sys/net/ipv4/ip_forward


