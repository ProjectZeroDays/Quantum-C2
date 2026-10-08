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
from quantum.ai.providers import (FREE_MODELS, UNCENSORED, free_models,
                                  provider_dashboard_state,
                                  provider_status, resolve_provider,
                                  sync_openrouter_models,
                                  uncensored_models)
from quantum.overlord.lifecycle import (LIFE_CYCLE, lifecycle_dashboard_state,
                                        lifecycle_recent_runs, loot_stats,
                                        phase_agent, run_lifecycle)

from quantum.recon.scan import ReconModule
from quantum.recon.intelx import (intelx_build_search_url, intelx_key,
                                  intelx_phonebook, intelx_recent_queries,
                                  intelx_search, intelx_tools,
                                  intelx_dashboard_state,
                                  intelx_dashboard_state_full,
                                  INTELX_TOOLS_CATALOG, SELECTOR_TYPES)
from quantum.recon.shadowdragon import (shadowdragon_dashboard_state,
                                        shadowdragon_license_status,
                                        shadowdragon_products,
                                        shadowdragon_query_plan,
                                        shadowdragon_source_matrix,
                                        SOURCE_FAMILIES, PRODUCTS,
                                        PIVOT_IDENTIFIERS)
from quantum.recon.darkowl import (darkowl_auth_header, darkowl_dashboard_state,
                                   darkowl_entity, darkowl_keys,
                                   darkowl_search, darkowl_test,
                                   ENDPOINTS, SEARCH_PARAMS)
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
from quantum.postexploit.cookies import (cookie_hosts, cookies_dashboard_state,
                                         delete_jar, import_jar, load_jar,
                                         parse_netscape, replay_session,
                                         save_jar)
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
from quantum.brute.hashes import (compute_hash, identify_hash, parse_pwdump,
                                  parse_hash_file, crack_hashes,
                                  brute_force_hashes, detect_hashcat,
                                  hashcat_command, hashcat_run, detect_john,
                                  john_command, john_show, john_run,
                                  cracking_dashboard_state,
                                  cracking_recent_runs, HASH_FORMATS,
                                  HASHCAT_MODES)
from quantum.brute.services import (brute_ftp, brute_http_basic,
                                    brute_http_form, brute_telnet,
                                    brute_smtp_auth, brute_pop3, brute_ssh,
                                    detect_hydra, hydra_command, hydra_run,
                                    services_dashboard_state,
                                    HYDRA_PROTOCOLS)
from quantum.brute.vaults import (xts_decrypt_unit, veracrypt_iterations,
                                  veracrypt_header_password_check,
                                  truecrypt_iterations,
                                  truecrypt_header_password_check,
                                  cryptomator_masterkey_check,
                                  zip_password_check, detect_7z, detect_unrar,
                                  detect_qpdf, detect_veracrypt,
                                  detect_truecrypt, sevenz_test_password,
                                  unrar_test_password, qpdf_test_password,
                                  archive_password_check,
                                  veracrypt_cli_command,
                                  veracrypt_test_password,
                                  truecrypt_test_password, vault_brute_force,
                                  vaults_dashboard_state, vault_recent_runs,
                                  VC_PRFs, TC_PRF_ORDER)
from quantum.ai.console import (list_agents, get_agent, save_agent,
                                delete_agent, deploy_agent,
                                active_deployment, list_skills, get_skill,
                                save_skill, delete_skill, list_workflows,
                                get_workflow, save_workflow, delete_workflow,
                                run_workflow, commands, task_queue,
                                clear_task, console_dashboard_state,
                                console_recent_events)
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
    "footprint_wipe_windows", "cookie_hosts", "cookies_dashboard_state",
    "delete_jar", "import_jar", "load_jar", "parse_netscape",
    "replay_session", "save_jar", "DataHarvester", "auto_parse_loot",
    "FEDERATION",
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
    "FREE_MODELS", "UNCENSORED", "free_models", "provider_dashboard_state",
    "provider_status", "resolve_provider", "sync_openrouter_models",
    "uncensored_models", "LIFE_CYCLE", "lifecycle_dashboard_state",
    "lifecycle_recent_runs", "loot_stats", "phase_agent", "run_lifecycle",
    "intelx_search", "intelx_phonebook", "intelx_tools",
    "intelx_dashboard_state", "intelx_dashboard_state_full",
    "intelx_recent_queries", "intelx_build_search_url", "intelx_key",
    "INTELX_TOOLS_CATALOG", "SELECTOR_TYPES",
    "shadowdragon_query_plan", "shadowdragon_source_matrix",
    "shadowdragon_products", "shadowdragon_license_status",
    "shadowdragon_dashboard_state", "SOURCE_FAMILIES", "PRODUCTS",
    "PIVOT_IDENTIFIERS", "darkowl_search", "darkowl_test",
    "darkowl_entity", "darkowl_auth_header", "darkowl_keys",
    "darkowl_dashboard_state", "ENDPOINTS", "SEARCH_PARAMS",
    "compute_hash", "identify_hash", "parse_pwdump", "parse_hash_file",
    "crack_hashes", "brute_force_hashes", "detect_hashcat",
    "hashcat_command", "hashcat_run", "detect_john", "john_command",
    "john_show", "john_run", "cracking_dashboard_state",
    "cracking_recent_runs", "HASH_FORMATS", "HASHCAT_MODES",
    "brute_ftp", "brute_http_basic", "brute_http_form", "brute_telnet",
    "brute_smtp_auth", "brute_pop3", "brute_ssh", "detect_hydra",
    "hydra_command", "hydra_run", "services_dashboard_state",
    "HYDRA_PROTOCOLS", "xts_decrypt_unit", "veracrypt_iterations",
    "veracrypt_header_password_check", "truecrypt_iterations",
    "truecrypt_header_password_check", "cryptomator_masterkey_check",
    "zip_password_check", "detect_7z", "detect_unrar", "detect_qpdf",
    "detect_veracrypt", "detect_truecrypt", "sevenz_test_password",
    "unrar_test_password", "qpdf_test_password", "archive_password_check",
    "veracrypt_cli_command", "veracrypt_test_password",
    "truecrypt_test_password", "vault_brute_force", "vaults_dashboard_state",
    "vault_recent_runs", "VC_PRFs", "TC_PRF_ORDER",
    "list_agents", "get_agent", "save_agent", "delete_agent",
    "deploy_agent", "active_deployment", "list_skills", "get_skill",
    "save_skill", "delete_skill", "list_workflows", "get_workflow",
    "save_workflow", "delete_workflow", "run_workflow", "commands",
    "task_queue", "clear_task", "console_dashboard_state",
    "console_recent_events",
]
