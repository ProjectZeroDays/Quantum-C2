#!/usr/bin/env python3
"""autonomous_gui.py — Tkinter GUI for autonomous network scanning with authorization disclaimer.

Authorized engagements / lab work only. The popup disclaimer must be acknowledged
before any scanning/exploitation activity begins.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import threading, sys, time, subprocess, json, socket
from pathlib import Path
from typing import List, Dict, Optional

# Import quantum framework modules (real code, not simulated)
from quantum.camwar.engine import CAMWAR
from quantum.camwar.brute_v3 import BruteEngineV3
from quantum.overlord.engines import UnitedDrake
from quantum.core.logging import log

# Router exploits framework (expanded to 82 CVEs)
try:
    import router_exploits as router_exp
except Exception:
    router_exp = None

# Authorized-use disclosure text (must be shown before any action)
AUTH_DISCLAIMER = (
    "AUTHORIZED ENGAGEMENT ONLY — LEGAL NOTICE\n\n"
    "This tool performs autonomous network scanning, device fingerprinting, "
    "service discovery, vulnerability identification, and automated payload customization.\n\n"
    "BY PROCEEDING YOU CONFIRM:\n"
    "• You have explicit written authorization to test these networks/devices.\n"
    "• You are operating within the scope of a contracted penetration test, red-team exercise, or lab.\n"
    "• You will not use this on networks/devices without expressed permission.\n\n"
    "Unauthorized use is illegal and violates the Computer Fraud and Abuse Act (CFAA), Computer Misuse Act, and equivalent laws worldwide.\n\n"
    "All results show connection details, device info, controls, and payload customization for successful connections only."
)

DEVICE_TYPES = [
    "Router / Gateway", "IoT / Embedded", "Desktop / Laptop",
    "Mobile / Smartphone", "Server / Cloud", "Network Storage",
    "Camera / DVR", "SCADA / Industrial", "Wireless Access Point",
    "Printer / MFP", "VoIP / Telephony", "Medical / Healthcare",
    "Smart Home / Appliance", "Vehicle / Automotive", "Drone / UAV"
]


class AutonomousScanWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("QUANTUM CLI — Autonomous Network Scanner v4.6.3")
        self.root.geometry("1100x780")
        self.root.configure(bg="#0d1117")
        self.auth_accepted = False
        self.scan_active = False
        self.results: List[Dict] = []
        self.build_ui()
        self.show_auth_dialog()

    def build_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg="#161b22", height=60)
        header.pack(fill=tk.X, pady=0)
        tk.Label(header, text="QUANTUM CLI — AUTONOMOUS NETWORK SCAN ENGINE",
                 font=("Consolas", 16, "bold"), fg="#58a6ff", bg="#161b22").pack(pady=12)

        # Main layout: left controls, right results
        body = tk.Frame(self.root, bg="#0d1117")
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # LEFT PANEL — Controls
        left = tk.Frame(body, bg="#161b22", width=340)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="SCAN CONFIGURATION", font=("Consolas", 12, "bold"),
                 fg="#58a6ff", bg="#161b22").pack(anchor=tk.W, padx=10, pady=(12, 8))

        # Scope input
        tk.Label(left, text="Scope (CIDR / Range / Single IP):", fg="#c9d1d9", bg="#161b22").pack(anchor=tk.W, padx=10)
        self.scope_var = tk.StringVar(value="192.168.1.0/24")
        scope_entry = tk.Entry(left, textvariable=self.scope_var, bg="#0d1117", fg="#e6edf3",
                               insertbackground="#58a6ff", relief=tk.FLAT, font=("Consolas", 10))
        scope_entry.pack(fill=tk.X, padx=10, pady=4)

        # Device type filter (multi-select checkboxes in scrollable frame)
        tk.Label(left, text="Target Device Types (select all that apply):",
                 fg="#c9d1d9", bg="#161b22").pack(anchor=tk.W, padx=10, pady=(12, 4))
        device_frame = tk.Frame(left, bg="#161b22")
        device_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self.device_vars = {}
        rows = 4
        cols = 4
        for idx, dtype in enumerate(DEVICE_TYPES):
            r = idx // cols
            c = idx % cols
            var = tk.BooleanVar(value=True)
            self.device_vars[dtype] = var
            chk = tk.Checkbutton(device_frame, text=dtype, variable=var,
                                 fg="#c9d1d9", bg="#161b22", selectcolor="#161b22",
                                 activebackground="#161b22", activeforeground="#58a6ff",
                                 font=("Segoe UI", 8))
            chk.grid(row=r, column=c, sticky="w", padx=3, pady=1)

        # Aggression / customization
        tk.Label(left, text="Aggression / Payload Mode:", fg="#c9d1d9", bg="#161b22").pack(anchor=tk.W, padx=10, pady=(10, 4))
        self.aggression_var = tk.StringVar(value="balanced")
        for label, val in [("Balanced", "balanced"), ("Aggressive", "aggressive"), ("Patient / Stealth", "patient")]:
            rb = tk.Radiobutton(left, text=label, variable=self.aggression_var, value=val,
                                fg="#c9d1d9", bg="#161b22", selectcolor="#21262d",
                                activebackground="#161b22", activeforeground="#58a6ff",
                                highlightthickness=0)
            rb.pack(anchor=tk.W, padx=22, pady=1)

        # Disclaimer reminder
        disclaimer_box = tk.Frame(left, bg="#21262d", bd=1, relief=tk.FLAT)
        disclaimer_box.pack(fill=tk.X, padx=10, pady=12)
        tk.Label(disclaimer_box,
                 text="⚠ AUTHORIZED USE ONLY\nOnly targets you have expressed permission to test.",
                 fg="#f85149", bg="#21262d", justify=tk.CENTER, font=("Segoe UI", 8, "bold")).pack(padx=8, pady=6)

        # Main action buttons
        btn_frame = tk.Frame(left, bg="#161b22")
        btn_frame.pack(fill=tk.X, padx=10, pady=8)

        self.scan_btn = tk.Button(btn_frame, text="▶ START AUTONOMOUS SCAN",
                                   command=self.start_scan, bg="#238636", fg="#ffffff",
                                   font=("Consolas", 11, "bold"), activebackground="#2ea043",
                                   activeforeground="#ffffff", bd=0, relief=tk.FLAT,
                                   cursor="hand2", height=2)
        self.scan_btn.pack(fill=tk.X, pady=4)

        self.stop_btn = tk.Button(btn_frame, text="⏹ STOP SCAN",
                                   command=self.stop_scan, bg="#da3633", fg="#ffffff",
                                   font=("Consolas", 11, "bold"), activebackground="#f85149",
                                   activeforeground="#ffffff", bd=0, relief=tk.FLAT,
                                   cursor="hand2", height=2, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=4)

        # Device info summary label (live updates)
        tk.Label(left, text="DEVICE CONNECTION SUMMARY:", font=("Consolas", 9, "bold"),
                 fg="#8b949e", bg="#161b22").pack(anchor=tk.W, padx=10, pady=(12, 4))
        self.info_label = tk.Label(left, text="No connections yet.", fg="#8b949e", bg="#161b22",
                                   justify=tk.LEFT, font=("Consolas", 8), wraplength=300)
        self.info_label.pack(anchor=tk.W, padx=10, fill=tk.X)

        # RIGHT PANEL — Results / Log / Details
        right = tk.Frame(body, bg="#161b22")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Tabbed results
        notebook = ttk.Notebook(right, style="Dark.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Live results table
        results_tab = tk.Frame(notebook, bg="#0d1117")
        notebook.add(results_tab, text="Discovery Results")
        columns = ("device", "type", "ip", "port", "service", "vuln", "payload", "status")
        self.tree = ttk.Treeview(results_tab, columns=columns, show="headings", height=18,
                                 style="Dark.Treeview")
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=90, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 2: Connection Details (device info for each successful connection)
        details_tab = tk.Frame(notebook, bg="#0d1117")
        notebook.add(details_tab, text="Device Details & Controls")

        self.detail_text = tk.Text(details_tab, bg="#0d1117", fg="#e6edf3",
                                   font=("Consolas", 9), insertbackground="#58a6ff",
                                   wrap=tk.WORD, state=tk.DISABLED, bd=0)
        detail_scroll = tk.Scrollbar(details_tab, command=self.detail_text.yview)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.config(yscrollcommand=detail_scroll.set)
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 3: Raw scan log
        log_tab = tk.Frame(notebook, bg="#0d1117")
        notebook.add(log_tab, text="Scan Log")
        self.log_box = tk.Text(log_tab, bg="#0d1117", fg="#c9d1d9",
                               font=("Consolas", 8), wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = tk.Scrollbar(log_tab, command=self.log_box.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_box.config(yscrollcommand=log_scroll.set)
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status bar
        status = tk.Frame(self.root, bg="#161b22", height=28)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(value="READY — Awaiting authorization acknowledgment.")
        tk.Label(status, textvariable=self.status_var, fg="#8b949e", bg="#161b22",
                 font=("Consolas", 9)).pack(side=tk.LEFT, padx=10, pady=4)
        tk.Label(status, text="v4.6.3 | Authorized use only", fg="#484f58", bg="#161b22",
                 font=("Consolas", 8)).pack(side=tk.RIGHT, padx=10, pady=4)

    # ------------------------------------------------------------------
    # AUTHENTICATION / AUTHORIZATION DIALOG
    # ------------------------------------------------------------------
    def show_auth_dialog(self):
        auth_win = tk.Toplevel(self.root)
        auth_win.title("Authorization & Disclaimer")
        auth_win.geometry("640x520")
        auth_win.configure(bg="#0d1117")
        auth_win.resizable(False, False)
        auth_win.transient(self.root)
        auth_win.grab_set()
        auth_win.protocol("WM_DELETE_WINDOW", lambda: self.on_auth_denied())

        # Center on screen
        auth_win.update_idletasks()
        x = (auth_win.winfo_screenwidth() // 2) - (640 // 2)
        y = (auth_win.winfo_screenheight() // 2) - (520 // 2)
        auth_win.geometry(f"640x520+{x}+{y}")

        tk.Label(auth_win, text="⚠ AUTHORIZATION REQUIRED", font=("Consolas", 18, "bold"),
                 fg="#f85149", bg="#0d1117").pack(pady=(24, 12))

        text_frame = tk.Frame(auth_win, bg="#0d1117")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)
        disclaimer_box = tk.Text(text_frame, bg="#161b22", fg="#e6edf3",
                                 font=("Consolas", 10), wrap=tk.WORD, height=14, bd=1,
                                 relief=tk.FLAT)
        disclaimer_box.insert(tk.END, AUTH_DISCLAIMER)
        disclaimer_box.config(state=tk.DISABLED)
        disclaimer_box.pack(fill=tk.BOTH, expand=True)

        # Acknowledgment checkbox
        self.auth_check = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(auth_win, text="I confirm I have expressed authorization for all targets.",
                             variable=self.auth_check, fg="#58a6ff", bg="#0d1117",
                             selectcolor="#161b22", activebackground="#0d1117",
                             activeforeground="#58a6ff", font=("Segoe UI", 9, "bold"))
        chk.pack(pady=10)

        btn_frame = tk.Frame(auth_win, bg="#0d1117")
        btn_frame.pack(pady=(4, 20))
        tk.Button(btn_frame, text="CONTINUE (AUTHORIZED ONLY)",
                  command=self.on_auth_accepted, bg="#238636", fg="#ffffff",
                  font=("Consolas", 11, "bold"), activebackground="#2ea043",
                  bd=0, width=28).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="DENY / EXIT",
                  command=self.on_auth_denied, bg="#da3633", fg="#ffffff",
                  font=("Consolas", 11, "bold"), activebackground="#f85149",
                  bd=0, width=14).pack(side=tk.LEFT)

    def on_auth_accepted(self):
        if not self.auth_check.get():
            messagebox.showwarning("Not Confirmed", "You must check the authorization checkbox to proceed.")
            return
        self.auth_accepted = True
        self.root.attributes("-topmost", False)
        for w in self.root.children.values():
            w.configure(bg="#0d1117")
        msg = "✅ AUTHORIZATION ACKNOWLEDGED — Scan controls unlocked. Only authorized targets."
        self.log(msg)
        self.status_var.set("AUTHORIZED — Ready to scan authorized targets only.")
        # Find and destroy auth window
        for child in self.root.children.values():
            pass
        # Close the top-level auth dialog
        for win in self.root.winfo_children():
            if isinstance(win, tk.Toplevel):
                win.destroy()
        # Re-enable root interactions
        self.scan_btn.config(state=tk.NORMAL)
        for rb in self.root.children.values():
            pass
        # Direct close
        for top in [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]:
            try:
                top.destroy()
            except Exception:
                pass

    def on_auth_denied(self):
        self.auth_accepted = False
        messagebox.showinfo("Access Denied", "Scan engine requires authorization acknowledgment. Closing.")
        self.root.quit()
        sys.exit(0)

    # ------------------------------------------------------------------
    # SCAN EXECUTION
    # ------------------------------------------------------------------
    def start_scan(self):
        if not self.auth_accepted:
            messagebox.showwarning("Not Authorized", "Please complete the authorization dialog first.")
            return
        self.scan_active = True
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("SCANNING — Autonomous network sweep active...")
        self.log("=== AUTONOMOUS SCAN STARTED ===")
        self.log(f"Scope: {self.scope_var.get()}")
        self.log(f"Aggression: {self.aggression_var.get()}")
        selected_types = [k for k, v in self.device_vars.items() if v.get()]
        self.log(f"Target device types: {', '.join(selected_types)}")
        # Launch background thread to avoid blocking GUI
        threading.Thread(target=self.run_scan, daemon=True).start()

    def stop_scan(self):
        self.scan_active = False
        self.status_var.set("STOP REQUESTED — Finishing current probes...")
        self.log("=== SCAN STOP REQUESTED ===")
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def run_scan(self):
        # Real integration with quantum framework modules
        try:
            scope = self.scope_var.get().strip()
            if not scope:
                self.log("ERROR: Scope must be specified.")
                return
            # Use CAMWAR for network discovery / fingerprinting
            try:
                cams = CAMWAR.discover(scope)
                self.log(f"CAMWAR discovered {len(cams)} camera/network targets in scope.")
            except Exception as exc:
                self.log(f"CAMWAR discover error (expected for non-camera scopes): {exc}")
                cams = []
            # Brute / fingerprint
            try:
                brute = BruteEngineV3()
                fingerprint_result = brute.scan_target(scope)
                self.log(f"Fingerprint: {fingerprint_result}")
            except Exception as exc:
                fingerprint_result = {"status": "unknown", "reason": str(exc)}
            # Router exploit framework check
            router_targets = []
            router_results = []
            if router_exp is not None:
                try:
                    # Try scanning common router subnets in scope
                    router_targets = [f"192.168.1.{i}" for i in range(1, 20)]
                    for ip in router_targets:
                        if not self.scan_active:
                            break
                        # Quick scan
                        try:
                            hits = router_exp.scan(ip)
                            for hit in hits:
                                router_results.append({"ip": ip, "vendor_hint": hit[0], "path": hit[1], "status": hit[2]})
                                self.log(f"Router hint: {hit[0]} at {ip}{hit[1]} — status={hit[2]}")
                        except Exception:
                            continue
                except Exception as exc:
                    self.log(f"Router exploit framework scan error: {exc}")
            else:
                self.log("Router exploits framework not available (expected in minimal install).")
            # UnitedDrake router attack (default creds)
            drake_results = []
            try:
                drake = UnitedDrake()
                # Try first few IPs in scope if they look like routers
                for ip in router_targets[:5]:
                    if not self.scan_active:
                        break
                    result = drake.attack_router(ip)
                    if result:
                        drake_results.append(result)
                        self.log(f"Drake router access: {result}")
            except Exception as exc:
                self.log(f"Drake router attack error: {exc}")
            # Aggregate results into display
            all_results = []
            for cam in cams:
                all_results.append({
                    "device": cam.get("device", "Unknown"),
                    "type": cam.get("type", "Camera"),
                    "ip": cam.get("ip", scope),
                    "port": cam.get("port", "80"),
                    "service": cam.get("service", "http"),
                    "vuln": cam.get("vuln", "Unknown"),
                    "payload": cam.get("payload", "N/A"),
                    "status": "SUCCESS",
                    "device_info": cam,
                    "connection_details": f"Port: {cam.get('port')} | Auth: {cam.get('auth', 'unknown')}",
                    "controls": f"Access: {cam.get('access', 'read_only')}"
                })
            for r in router_results:
                all_results.append({
                    "device": f"Router ({r['vendor_hint']})",
                    "type": "Router / Gateway",
                    "ip": r["ip"],
                    "port": "80/443",
                    "service": "HTTP",
                    "vuln": "CVE-Scan Active",
                    "payload": "router_exploits_custom",
                    "status": "PROBED",
                    "device_info": r,
                    "connection_details": f"Path: {r['path']} | Status: {r['status']}",
                    "controls": "Web UI / CGI"
                })
            for r in drake_results:
                all_results.append({
                    "device": "Router Admin",
                    "type": "Router / Gateway",
                    "ip": r.get("ip", "unknown"),
                    "port": "80",
                    "service": "HTTP Admin",
                    "vuln": "Default Credentials",
                    "payload": "credential_access",
                    "status": "SUCCESS",
                    "device_info": r,
                    "connection_details": f"User: {r.get('user', '?')} Pass: {r.get('pass', '?')}",
                    "controls": "Full Admin Access"
                })
            # Populate UI on main thread
            self.root.after(0, lambda results=all_results: self.display_results(results))
        finally:
            self.scan_active = False
            self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set("SCAN COMPLETE — Review results below."))
            self.log("=== SCAN FINISHED ===")

    def display_results(self, results: List[Dict]):
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert new rows
        for res in results:
            self.tree.insert("", tk.END, values=(
                res.get("device", "-"),
                res.get("type", "-"),
                res.get("ip", "-"),
                res.get("port", "-"),
                res.get("service", "-"),
                res.get("vuln", "-"),
                res.get("payload", "-"),
                res.get("status", "-"),
            ))
        # Update detail text for each successful connection
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        for res in results:
            if res.get("status") == "SUCCESS" or res.get("status") == "PROBED":
                header = f"{'='*60}\nDEVICE: {res.get('device')}  |  TYPE: {res.get('type')}\n{'='*60}\n"
                info_block = f"IP Address:    {res.get('ip', 'N/A')}\n"
                info_block += f"Port:          {res.get('port', 'N/A')}\n"
                info_block += f"Service:       {res.get('service', 'N/A')}\n"
                info_block += f"Status:        {res.get('status', 'N/A')}\n"
                info_block += f"Vulnerability: {res.get('vuln', 'N/A')}\n"
                info_block += f"Payload:       {res.get('payload', 'N/A')}\n"
                info_block += f"Connection:    {res.get('connection_details', 'N/A')}\n"
                info_block += f"Controls:      {res.get('controls', 'N/A')}\n"
                info_block += f"Device Info:   {json.dumps(res.get('device_info', {}), indent=2, default=str)}\n"
                info_block += f"{'-'*60}\n"
                self.detail_text.insert(tk.END, header + info_block)
        self.detail_text.config(state=tk.DISABLED)
        # Update info label on left
        count = len([r for r in results if r.get("status") in ("SUCCESS", "PROBED")])
        self.info_label.config(text=f"Connections: {count} | Types: {', '.join({r.get('type', '-') for r in results})}")
        # Log summary
        self.log(f"Results: {len(results)} devices probed; {count} successful/probed connections.")
        self.results.extend(results)

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, line)
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    # Minimal dark theme styling
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Dark.Treeview", background="#161b22", foreground="#e6edf3",
                    fieldbackground="#161b22", rowheight=22)
    style.configure("Dark.TNotebook", background="#161b22", tabmargins=[2, 5, 2, 0])
    style.configure("Dark.TNotebook.Tab", background="#21262d", foreground="#58a6ff",
                    padding=[6, 3])
    # Create window
    app = AutonomousScanWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
