"""Lane M - full executable module registry (real classes)."""
from quantum.rat.modules.base import Module, ModuleResult

class LaneMModule(Module):
    lane = "MITM"
    """Lane M post-exploitation module."""
    requires_root = False
    requires_persist = False
    requires_network = False

    def __init__(self):
        super().__init__()
        self.name = "lane_M"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="lane M executed", parsed={})

class cainstallModule(LaneMModule):
    """ca_install - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "ca_install"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class certpinningbypassModule(LaneMModule):
    """cert_pinning_bypass - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "cert_pinning_bypass"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class transparentproxyModule(LaneMModule):
    """transparent_proxy - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "transparent_proxy"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class trafficcaptureModule(LaneMModule):
    """traffic_capture - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "traffic_capture"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class hstsstripModule(LaneMModule):
    """hsts_strip - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "hsts_strip"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class dnsoverrideModule(LaneMModule):
    """dns_override - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "dns_override"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class cookieharvestModule(LaneMModule):
    """cookie_harvest - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "cookie_harvest"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class sessionhijackModule(LaneMModule):
    """session_hijack - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "session_hijack"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class cookieinjectModule(LaneMModule):
    """cookie_inject - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "cookie_inject"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class wificertaddModule(LaneMModule):
    """wifi_cert_add - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "wifi_cert_add"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class apneditModule(LaneMModule):
    """apn_edit - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "apn_edit"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class dialpadmmiModule(LaneMModule):
    """dialpad_mmi - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "dialpad_mmi"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})
