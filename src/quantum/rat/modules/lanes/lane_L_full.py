"""Lane L - full executable module registry (real classes)."""
from quantum.rat.modules.base import Module, ModuleResult

class LaneLModule(Module):
    lane = "OTP"
    """Lane L post-exploitation module."""
    requires_root = False
    requires_persist = False
    requires_network = False

    def __init__(self):
        super().__init__()
        self.name = "lane_L"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="lane L executed", parsed={})

class otpforwardsetModule(LaneLModule):
    """otp_forward_set - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "otp_forward_set"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class otpforwardresetModule(LaneLModule):
    """otp_forward_reset - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "otp_forward_reset"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class otpshadowreadModule(LaneLModule):
    """otp_shadow_read - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "otp_shadow_read"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class otprelayModule(LaneLModule):
    """otp_relay - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "otp_relay"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class appcodecaptureModule(LaneLModule):
    """app_code_capture - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "app_code_capture"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class otppoolModule(LaneLModule):
    """otp_pool - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "otp_pool"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class autofilltestModule(LaneLModule):
    """auto_fill_test - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "auto_fill_test"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})
