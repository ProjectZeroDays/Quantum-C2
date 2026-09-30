"""
Compliance engine for Quantum C2.
Implements NIST 800-53, FedRAMP, and other compliance frameworks.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum


logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    NIST_800_53 = "NIST_800_53"
    NIST_800_171 = "NIST_800_171"
    FedRAMP = "FedRAMP"
    PCI_DSS = "PCI_DSS"
    HIPAA = "HIPAA"
    SOC2 = "SOC2"
    ISO_27001 = "ISO_27001"
    CJIS = "CJIS"


@dataclass
class Control:
    """Represents a compliance control."""
    control_id: str
    family: str
    title: str
    description: str
    requirements: List[str]
    assessment_procedures: List[str]
    severity: str
    baseline: str


@dataclass
class ComplianceResult:
    """Result of compliance assessment."""
    framework: str
    control_id: str
    status: str  # "compliant", "non-compliant", "partial", "not-assessed"
    evidence: str
    findings: List[str]
    remediation: str
    assessed_at: str
    assessed_by: str


class ComplianceEngine:
    """Main compliance engine for Quantum C2."""
    
    def __init__(self):
        self.controls: Dict[str, Control] = {}
        self.results: List[ComplianceResult] = []
        self._load_controls()
    
    def _load_controls(self):
        """Load compliance controls from the comprehensive database."""
        from .compliance_controls_db import generate_comprehensive_controls
        self.controls = generate_comprehensive_controls()
        
        self.controls["AC-2"] = Control(
            control_id="AC-2",
            family="Access Control",
            title="Account Management",
            description="The organization manages information system accounts.",
            requirements=[
                "Identify account types",
                "Establish conditions for group/role membership",
                "Assign account managers",
                "Require approvals for requests"
            ],
            assessment_procedures=[
                "Interview personnel regarding account management",
                "Examine account management procedures",
                "Verify account approvals exist"
            ],
            severity="high",
            baseline="All"
        )
        
        self.controls["AU-1"] = Control(
            control_id="AU-1",
            family="Audit and Accountability",
            title="Audit and Accountability Policy and Procedures",
            description="The organization develops, documents, and disseminates audit and accountability policy.",
            requirements=[
                "Develop audit policy",
                "Document audit procedures",
                "Review and update policy annually"
            ],
            assessment_procedures=[
                "Interview personnel regarding audit policy",
                "Examine audit policy and procedures",
                "Verify policy is current"
            ],
            severity="high",
            baseline="All"
        )
        
        self.controls["CM-1"] = Control(
            control_id="CM-1",
            family="Configuration Management",
            title="Configuration Management Policy and Procedures",
            description="The organization develops, documents, and disseminates configuration management policy.",
            requirements=[
                "Develop configuration management policy",
                "Document procedures",
                "Review and update annually"
            ],
            assessment_procedures=[
                "Interview personnel regarding configuration management",
                "Examine configuration management policy",
                "Verify policy is current"
            ],
            severity="high",
            baseline="All"
        )
        
        self.controls["IA-1"] = Control(
            control_id="IA-1",
            family="Identification and Authentication",
            title="Identification and Authentication Policy and Procedures",
            description="The organization develops, documents, and disseminates identification and authentication policy.",
            requirements=[
                "Develop identification and authentication policy",
                "Document procedures",
                "Review and update annually"
            ],
            assessment_procedures=[
                "Interview personnel regarding identification and authentication",
                "Examine policy and procedures",
                "Verify policy is current"
            ],
            severity="high",
            baseline="All"
        )
        
        self.controls["SC-1"] = Control(
            control_id="SC-1",
            family="System and Communications Protection",
            title="System and Communications Protection Policy and Procedures",
            description="The organization develops, documents, and disseminates system and communications protection policy.",
            requirements=[
                "Develop system protection policy",
                "Document procedures",
                "Review and update annually"
            ],
            assessment_procedures=[
                "Interview personnel regarding system protection",
                "Examine policy and procedures",
                "Verify policy is current"
            ],
            severity="high",
            baseline="All"
        )
        
        self.controls["SI-1"] = Control(
            control_id="SI-1",
            family="System and Information Integrity",
            title="System and Information Integrity Policy and Procedures",
            description="The organization develops, documents, and disseminates system and information integrity policy.",
            requirements=[
                "Develop system integrity policy",
                "Document procedures",
                "Review and update annually"
            ],
            assessment_procedures=[
                "Interview personnel regarding system integrity",
                "Examine policy and procedures",
                "Verify policy is current"
            ],
            severity="high",
            baseline="All"
        )
        
        # Additional NIST 800-53 Controls
        self.controls["AC-3"] = Control(
            control_id="AC-3",
            family="Access Control",
            title="Access Enforcement",
            description="The organization enforces authorized access controls.",
            requirements=["Enforce access controls", "Implement discretionary access control", "Implement mandatory access control"],
            assessment_procedures=["Examine access enforcement mechanisms", "Test access controls"],
            severity="high",
            baseline="All"
        )
        
        self.controls["AC-4"] = Control(
            control_id="AC-4",
            family="Access Control",
            title="Information Flow Enforcement",
            description="The organization controls information flows within the system.",
            requirements=["Control information flows", "Implement flow control policies"],
            assessment_procedures=["Examine flow control mechanisms"],
            severity="high",
            baseline="High"
        )
        
        self.controls["AC-5"] = Control(
            control_id="AC-5",
            family="Access Control",
            title="Separation of Duties",
            description="The organization separates duties of individuals.",
            requirements=["Separate duties", "Document separations"],
            assessment_procedures=["Interview personnel", "Examine duty separation documentation"],
            severity="medium",
            baseline="High"
        )
        
        self.controls["AC-6"] = Control(
            control_id="AC-6",
            family="Access Control",
            title="Least Privilege",
            description="The organization employs the principle of least privilege.",
            requirements=["Implement least privilege", "Review privileges periodically"],
            assessment_procedures=["Examine privilege assignments", "Verify least privilege enforcement"],
            severity="high",
            baseline="High"
        )
        
        self.controls["AC-7"] = Control(
            control_id="AC-7",
            family="Access Control",
            title="Unsuccessful Logon",
            description="The organization enforces unsuccessful logon procedures.",
            requirements=["Lock accounts after failed attempts", "Notify users of lockouts"],
            assessment_procedures=["Test lockout mechanism", "Verify notifications"],
            severity="medium",
            baseline="All"
        )
        
        self.controls["AC-8"] = Control(
            control_id="AC-8",
            family="Access Control",
            title="System Use Notification",
            description="The organization displays system use notification.",
            requirements=["Display notification before access", "Use standard message"],
            assessment_procedures=["Verify notification display", "Review notification content"],
            severity="medium",
            baseline="All"
        )
        
        self.controls["AT-1"] = Control(
            control_id="AT-1",
            family="Awareness and Training",
            title="Security Awareness and Training Policy",
            description="The organization develops security awareness and training policy.",
            requirements=["Develop awareness policy", "Provide security training"],
            assessment_procedures=["Examine training program", "Verify training completion"],
            severity="medium",
            baseline="All"
        )
        
        self.controls["AU-2"] = Control(
            control_id="AU-2",
            family="Audit and Accountability",
            title="Audit Events",
            description="The organization determines audit capabilities.",
            requirements=["Determine auditable events", "Configure audit logging"],
            assessment_procedures=["Review audit event criteria", "Verify audit logging"],
            severity="high",
            baseline="All"
        )
        
        self.controls["AU-3"] = Control(
            control_id="AU-3",
            family="Audit and Accountability",
            title="Content of Audit Records",
            description="The organization produces audit records containing sufficient information.",
            requirements=["Include user identity", "Include events", "Include timestamps"],
            assessment_procedures=["Examine audit records", "Verify completeness"],
            severity="high",
            baseline="All"
        )
        
        self.controls["CA-1"] = Control(
            control_id="CA-1",
            family="Assessment, Authorization, and Monitoring",
            title="Security Assessment and Authorization Policy",
            description="The organization develops security assessment and authorization policy.",
            requirements=["Develop assessment policy", "Conduct regular assessments"],
            assessment_procedures=["Examine assessment procedures", "Verify authorization"],
            severity="high",
            baseline="All"
        )
        
        self.controls["CM-2"] = Control(
            control_id="CM-2",
            family="Configuration Management",
            title="Baseline Configuration",
            description="The organization develops and maintains baseline configurations.",
            requirements=["Establish baselines", "Update baselines"],
            assessment_procedures=["Review baseline configurations", "Verify updates"],
            severity="high",
            baseline="All"
        )
        
        self.controls["CM-6"] = Control(
            control_id="CM-6",
            family="Configuration Management",
            title="Configuration Settings",
            description="The organization establishes and documents configuration settings.",
            requirements=["Establish configuration settings", "Implement settings"],
            assessment_procedures=["Review configuration settings", "Verify implementation"],
            severity="high",
            baseline="All"
        )
        
        self.controls["CP-1"] = Control(
            control_id="CP-1",
            family="Contingency Planning",
            title="Contingency Plan Policy and Procedures",
            description="The organization develops contingency plan policy.",
            requirements=["Develop contingency plan", "Test plan annually"],
            assessment_procedures=["Review contingency plan", "Verify testing"],
            severity="high",
            baseline="All"
        )
        
        self.controls["IA-2"] = Control(
            control_id="IA-2",
            family="Identification and Authentication",
            title="Identification and Authentication (Organizational Users)",
            description="The organization identifies and authenticates organizational users.",
            requirements=["Authenticate users", "Use MFA for privileged access"],
            assessment_procedures=["Test authentication mechanisms", "Verify MFA implementation"],
            severity="high",
            baseline="All"
        )
        
        self.controls["IR-1"] = Control(
            control_id="IR-1",
            family="Incident Response",
            title="Incident Response Policy and Procedures",
            description="The organization develops incident response policy.",
            requirements=["Develop incident response plan", "Train incident responders"],
            assessment_procedures=["Review incident response plan", "Verify training"],
            severity="high",
            baseline="All"
        )
        
        self.controls["MA-1"] = Control(
            control_id="MA-1",
            family="Maintenance",
            title="Maintenance Policy and Procedures",
            description="The organization develops maintenance policy.",
            requirements=["Develop maintenance policy", "Conduct scheduled maintenance"],
            assessment_procedures=["Review maintenance procedures", "Verify scheduling"],
            severity="medium",
            baseline="All"
        )
        
        self.controls["MP-1"] = Control(
            control_id="MP-1",
            family="Media Protection",
            title="Media Protection Policy and Procedures",
            description="The organization develops media protection policy.",
            requirements=["Develop media protection policy", "Protect media"],
            assessment_procedures=["Review media protection procedures", "Verify protection"],
            severity="medium",
            baseline="All"
        )
        
        self.controls["PE-1"] = Control(
            control_id="PE-1",
            family="Physical and Environmental Protection",
            title="Physical and Environmental Protection Policy",
            description="The organization develops physical protection policy.",
            requirements=["Develop physical protection policy", "Control physical access"],
            assessment_procedures=["Review physical security", "Verify access controls"],
            severity="high",
            baseline="All"
        )
        
        self.controls["PL-1"] = Control(
            control_id="PL-1",
            family="Planning",
            title="Security Planning Policy and Procedures",
            description="The organization develops security planning policy.",
            requirements=["Develop security plans", "Coordinate with similar activities"],
            assessment_procedures=["Review security plans", "Verify coordination"],
            severity="medium",
            baseline="All"
        )
        
        self.controls["PS-1"] = Control(
            control_id="PS-1",
            family="Personnel Security",
            title="Personnel Security Policy and Procedures",
            description="The organization develops personnel security policy.",
            requirements=["Conduct background checks", "Terminate access upon separation"],
            assessment_procedures=["Review personnel security procedures", "Verify background checks"],
            severity="medium",
            baseline="All"
        )
        
        self.controls["RA-1"] = Control(
            control_id="RA-1",
            family="Risk Assessment",
            title="Risk Assessment Policy and Procedures",
            description="The organization develops risk assessment policy.",
            requirements=["Conduct risk assessments", "Document risk findings"],
            assessment_procedures=["Review risk assessment procedures", "Verify documentation"],
            severity="high",
            baseline="All"
        )
        
        self.controls["SA-1"] = Control(
            control_id="SA-1",
            family="System and Services Acquisition",
            title="System and Services Acquisition Policy",
            description="The organization develops acquisition policy.",
            requirements=["Include security requirements", "Verify vendor compliance"],
            assessment_procedures=["Review acquisition procedures", "Verify vendor assessments"],
            severity="high",
            baseline="All"
        )
        
        self.controls["SC-2"] = Control(
            control_id="SC-2",
            family="System and Communications Protection",
            title="Application Partitioning",
            description="The organization separates user functions from information system management functions.",
            requirements=["Partition user functions", "Separate management functions"],
            assessment_procedures=["Examine partitioning mechanisms", "Verify separation"],
            severity="medium",
            baseline="High"
        )
        
        self.controls["SC-7"] = Control(
            control_id="SC-7",
            family="System and Communications Protection",
            title="Boundary Protection",
            description="The organization monitors and controls communications at the external boundary.",
            requirements=["Monitor boundary traffic", "Implement boundary protection"],
            assessment_procedures=["Test boundary protection", "Review monitoring"],
            severity="high",
            baseline="All"
        )
        
        self.controls["SC-12"] = Control(
            control_id="SC-12",
            family="System and Communications Protection",
            title="Cryptographic Key Establishment and Management",
            description="The organization establishes and manages cryptographic keys.",
            requirements=["Generate keys using validated modules", "Protect keys"],
            assessment_procedures=["Review key management procedures", "Verify key protection"],
            severity="high",
            baseline="High"
        )
        
        self.controls["SC-13"] = Control(
            control_id="SC-13",
            family="System and Communications Protection",
            title="Cryptographic Protection",
            description="The organization implements cryptographic algorithms and key management.",
            requirements=["Use FIPS-approved algorithms", "Implement key management"],
            assessment_procedures=["Verify algorithm implementation", "Review key management"],
            severity="high",
            baseline="All"
        )
        
        self.controls["SC-21"] = Control(
            control_id="SC-21",
            family="System and Communications Protection",
            title="Authentication and Authorization Feedback",
            description="The organization provides authentication and authorization feedback.",
            requirements=["Provide feedback to users", "Confirm security bindings"],
            assessment_procedures=["Review feedback mechanisms", "Verify confirmation"],
            severity="medium",
            baseline="High"
        )
        
        self.controls["SC-28"] = Control(
            control_id="SC-28",
            family="System and Communications Protection",
            title="Protection of Information at Rest",
            description="The organization protects the confidentiality and integrity of information at rest.",
            requirements=["Encrypt stored data", "Implement access controls"],
            assessment_procedures=["Verify encryption implementation", "Review access controls"],
            severity="high",
            baseline="High"
        )
        
        self.controls["SI-2"] = Control(
            control_id="SI-2",
            family="System and Information Integrity",
            title="Flaw Remediation",
            description="The organization identifies, reports, and corrects information system flaws.",
            requirements=["Identify flaws", "Remediate within timeframes"],
            assessment_procedures=["Review flaw remediation process", "Verify timely fixes"],
            severity="high",
            baseline="All"
        )
        
        self.controls["SI-3"] = Control(
            control_id="SI-3",
            family="System and Information Integrity",
            title="Malicious Code Protection",
            description="The organization implements malicious code protection.",
            requirements=["Implement anti-malware", "Update protections"],
            assessment_procedures=["Review anti-malware implementation", "Verify updates"],
            severity="high",
            baseline="All"
        )
        
        self.controls["SI-4"] = Control(
            control_id="SI-4",
            family="System and Information Integrity",
            title="Information System Monitoring",
            description="The organization monitors the information system.",
            requirements=["Implement monitoring tools", "Analyze activity"],
            assessment_procedures=["Review monitoring capabilities", "Verify analysis"],
            severity="high",
            baseline="All"
        )
        
        self.controls["SI-5"] = Control(
            control_id="SI-5",
            family="System and Information Integrity",
            title="Security Alerts, Advisories, and Directives",
            description="The organization receives security alerts and advisories.",
            requirements=["Receive alerts", "Respond to directives"],
            assessment_procedures=["Review alert handling", "Verify response procedures"],
            severity="high",
            baseline="All"
        )
    
    def get_control(self, control_id: str) -> Optional[Control]:
        """Get a specific control by ID."""
        return self.controls.get(control_id)
    
    def get_controls_by_family(self, family: str) -> List[Control]:
        """Get all controls in a family."""
        return [c for c in self.controls.values() if c.family == family]
    
    def get_all_controls(self) -> List[Control]:
        """Get all controls."""
        return list(self.controls.values())
    
    def assess_control(self, control_id: str, evidence: str = "", 
                       findings: Optional[List[str]] = None,
                       remediation: str = "",
                       assessed_by: str = "system") -> Optional[ComplianceResult]:
        """Assess a control against evidence."""
        control = self.get_control(control_id)
        if not control:
            logger.warning(f"Control {control_id} not found")
            return None
        
        # Determine compliance status
        status = self._determine_status(control, evidence)
        
        result = ComplianceResult(
            framework=ComplianceFramework.NIST_800_53.value,
            control_id=control_id,
            status=status,
            evidence=evidence,
            findings=findings or [],
            remediation=remediation,
            assessed_at=datetime.now(timezone.utc).isoformat(),
            assessed_by=assessed_by
        )
        
        self.results.append(result)
        return result
    
    def _determine_status(self, control: Control, evidence: str) -> str:
        """Determine compliance status based on evidence."""
        if not evidence:
            return "not-assessed"
        
        # Simple heuristic - in production, use more sophisticated logic
        evidence_lower = evidence.lower()
        
        if any(req.lower() in evidence_lower for req in control.requirements[:2]):
            return "compliant"
        elif any(req.lower() in evidence_lower for req in control.requirements):
            return "partial"
        else:
            return "non-compliant"
    
    def run_full_assessment(self, evidence: Dict[str, str], 
                           assessed_by: str = "system") -> List[ComplianceResult]:
        """Run full compliance assessment against all controls."""
        results = []
        for control_id in self.controls.keys():
            control_evidence = evidence.get(control_id, "")
            result = self.assess_control(control_id, control_evidence, assessed_by=assessed_by)
            if result:
                results.append(result)
        return results
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get overall compliance summary."""
        if not self.results:
            return {"status": "no_assessment", "score": 0}
        
        total = len(self.results)
        compliant = sum(1 for r in self.results if r.status == "compliant")
        partial = sum(1 for r in self.results if r.status == "partial")
        non_compliant = sum(1 for r in self.results if r.status == "non-compliant")
        not_assessed = sum(1 for r in self.results if r.status == "not-assessed")
        
        # Calculate compliance score
        score = (compliant * 100 + partial * 50) / total if total > 0 else 0
        
        return {
            "total_controls": total,
            "compliant": compliant,
            "partial": partial,
            "non_compliant": non_compliant,
            "not_assessed": not_assessed,
            "compliance_score": round(score, 2),
            "status": "compliant" if score >= 90 else "partial" if score >= 70 else "non-compliant",
            "last_assessed": self.results[-1].assessed_at if self.results else None
        }
    
    def get_results_by_family(self, family: str) -> List[ComplianceResult]:
        """Get results filtered by family."""
        family_controls = {c.control_id for c in self.get_controls_by_family(family)}
        return [r for r in self.results if r.control_id in family_controls]
    
    def export_results(self, format: str = "json") -> str:
        """Export compliance results."""
        if format == "json":
            return json.dumps([asdict(r) for r in self.results], indent=2)
        elif format == "csv":
            lines = ["control_id,framework,status,evidence,findings,remediation,assessed_at,assessed_by"]
            for r in self.results:
                lines.append(f"{r.control_id},{r.framework},{r.status},{r.evidence},{'; '.join(r.findings)},{r.remediation},{r.assessed_at},{r.assessed_by}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Singleton instance
_compliance_engine = None


def get_compliance_engine() -> ComplianceEngine:
    """Get or create compliance engine singleton."""
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    return _compliance_engine


def assess_compliance(evidence: Dict[str, str], framework: str = "NIST_800_53") -> Dict[str, Any]:
    """Convenience function to assess compliance."""
    engine = get_compliance_engine()
    results = engine.run_full_assessment(evidence)
    return engine.get_compliance_summary()


if __name__ == "__main__":
    # Run compliance assessment
    engine = ComplianceEngine()
    
    # Example evidence
    evidence = {
        "AC-1": "Access control policy developed and documented. Procedures established for account management. Policy reviewed annually.",
        "AC-2": "Account management procedures in place. All accounts have assigned managers. Approval process documented.",
        "AU-1": "Audit policy developed. Audit procedures documented. Annual review conducted.",
        "CM-1": "Configuration management policy exists. Procedures documented. Review schedule established.",
        "IA-1": "Identification and authentication policy developed. Multi-factor authentication implemented.",
        "SC-1": "System protection policy in place. Communications protection procedures documented.",
        "SI-1": "System integrity policy developed. Malware protection implemented. Integrity monitoring in place."
    }
    
    results = engine.run_full_assessment(evidence)
    summary = engine.get_compliance_summary()
    
    print("Compliance Assessment Summary:")
    print(f"  Score: {summary['compliance_score']}%")
    print(f"  Status: {summary['status']}")
    print(f"  Compliant: {summary['compliant']}/{summary['total_controls']}")
    print(f"  Partial: {summary['partial']}")
    print(f"  Non-compliant: {summary['non_compliant']}")
    print(f"  Not assessed: {summary['not_assessed']}")
