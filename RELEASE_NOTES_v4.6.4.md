## v4.6.4 Release Notes

### Router Exploit Framework (82 CVEs)
- Expanded registry from 44 -> 82 real CVEs
- Covers Tenda, Wavlink, D-Link, Belkin, TP-Link, Netgear, Linksys, MikroTik, Cisco, ASUS, Realtek SDK, Netis, TOTOLINK, Edimax, Buffalo, Xiaomi, Zyxel, Huawei, ZTE, pfSense, OpenWrt
- Real cmd_inject, overflow, traversal techniques (no simulated code)

### CLI Integration
- New routerexploit command added to quantum_cli.py

### Autonomous Network Scan GUI (agents/quantumcli-desktop/autonomous_gui.py)
- Popup authorization disclaimer (must agree before scan)
- Autonomous scan button (CAMWAR + BruteEngineV3 + router_exploits + UnitedDrake)
- OS/device fingerprinting, service/vuln discovery
- Automated payload customization per device type
- Device controls, connection details, device info for all 15 device categories
- Only authorized targets — legal notice enforced

### Assets
- APK builds (full + limited)
- Payload archives (quantum-exploits-v4.6.4.zip, quantum-payloads-v4.6.4.zip)
- Lock files (payloads.lock.json, PLATFORM_INDEX.json)
- Individual executable artifacts included
