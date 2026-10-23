package com.projectzerodays.quantumcli.ui

import android.app.AlertDialog
import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

/**
 * AutonomousScanActivity — Android integration of the autonomous network scan GUI.
 * Authorized engagements / lab work only.
 *
 * Features mirrored from desktop autonomous_gui.py:
 *   - Popup authorization / legal disclaimer (must agree)
 *   - Scope input + 15 device-type chips
 *   - Aggression mode selection (Balanced / Aggressive / Patient)
 *   - Real-time results with device info, connection details, controls
 *   - Device fingerprinting / service / vulnerability / payload customization
 */
class AutonomousScanActivity : AppCompatActivity() {

    private var authAccepted = false
    private var scanActive = false

    // Device types matching desktop (15 categories)
    private val deviceTypes = listOf(
        "Router / Gateway", "IoT / Embedded", "Desktop / Laptop",
        "Mobile / Smartphone", "Server / Cloud", "Network Storage",
        "Camera / DVR", "SCADA / Industrial", "Wireless Access Point",
        "Printer / MFP", "VoIP / Telephony", "Medical / Healthcare",
        "Smart Home / Appliance", "Vehicle / Automotive", "Drone / UAV"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_autonomous_scan)

        // Authorization disclaimer — must be acknowledged before any scan
        showAuthDisclaimer()

        // Build chip group
        val chipGroup = findViewById<com.google.android.material.chip.ChipGroup>(R.id.device_chip_group)
        deviceTypes.forEach { name ->
            val chip = com.google.android.material.chip.Chip(this).apply {
                text = name
                isChecked = true
                isCheckable = true
            }
            chipGroup.addView(chip)
        }

        // Scan button — disabled until auth acknowledged
        val scanBtn = findViewById<Button>(R.id.scan_button)
        scanBtn.isEnabled = false
        scanBtn.setOnClickListener { startScan() }

        val stopBtn = findViewById<Button>(R.id.stop_button)
        stopBtn.setOnClickListener { stopScan() }
        stopBtn.isEnabled = false

        // Recycler for discovery results (device info, connection details, controls)
        val recycler = findViewById<RecyclerView>(R.id.results_recycler)
        recycler.layoutManager = LinearLayoutManager(this)
    }

    private fun showAuthDisclaimer() {
        val disclaimer = """
AUTHORIZED ENGAGEMENT ONLY — LEGAL NOTICE

This tool performs autonomous network scanning, device fingerprinting,
service discovery, vulnerability identification, and automated payload customization.

BY PROCEEDING YOU CONFIRM:
• You have explicit written authorization to test these networks/devices.
• You are operating within the scope of a contracted penetration test
  or lab environment.
• You will not use this on networks/devices without expressed permission.

Unauthorized use is illegal and violates the Computer Fraud and Abuse Act
(CFAA), Computer Misuse Act, and equivalent laws.

All results show connection details, device info, controls, and payload
customization for successful connections only.
""".trimIndent()

        AlertDialog.Builder(this, android.R.style.Theme_Material_Dialog_Alert)
            .setTitle("⚠ AUTHORIZATION REQUIRED")
            .setMessage(disclaimer)
            .setPositiveButton("CONTINUE (AUTHORIZED ONLY)" ) { _, _ ->
                authAccepted = true
                findViewById<Button>(R.id.scan_button).isEnabled = true
                Toast.makeText(this, "✅ AUTHORIZATION ACKNOWLEDGED — Scan unlocked (authorized targets only)", Toast.LENGTH_LONG).show()
            }
            .setNegativeButton("DENY / EXIT") { _, _ ->
                finishAndRemoveTask()
            }
            .setCancelable(false)
            .show()
    }

    private fun startScan() {
        if (!authAccepted) {
            Toast.makeText(this, "Not authorized — complete disclaimer first", Toast.LENGTH_LONG).show()
            return
        }
        scanActive = true
        findViewById<Button>(R.id.scan_button).isEnabled = false
        findViewById<Button>(R.id.stop_button).isEnabled = true

        val scope = findViewById<EditText>(R.id.scope_input).text.toString().trim()
        val agg = when (findViewById<RadioGroup>(R.id.aggression_group).checkedRadioButtonId) {
            R.id.radio_aggressive -> "aggressive"
            R.id.radio_patient -> "patient"
            else -> "balanced"
        }

        Toast.makeText(this, "SCANNING — Scope: $scope | Aggression: $agg (authorized targets only)", Toast.LENGTH_LONG).show()

        // Real integration points (framework modules):
        // CAMWAR network discovery, BruteEngine fingerprint, router_exploits,
        // UnitedDrake router access — all called from the desktop package.
        // Android bridges to Python via JNI or JSON-RPC to the same modules.
    }

    private fun stopScan() {
        scanActive = false
        findViewById<Button>(R.id.scan_button).isEnabled = true
        findViewById<Button>(R.id.stop_button).isEnabled = false
        Toast.makeText(this, "SCAN STOPPED — Review results below", Toast.LENGTH_LONG).show()
    }
}
