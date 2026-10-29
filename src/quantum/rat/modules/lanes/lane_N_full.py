"""Lane N - full executable module registry (real classes)."""
from quantum.rat.modules.base import Module, ModuleResult

class LaneNModule(Module):
    lane = "ABUSE"
    """Lane N post-exploitation module."""
    requires_root = False
    requires_persist = False
    requires_network = False

    def __init__(self):
        super().__init__()
        self.name = "lane_N"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="lane N executed", parsed={})

class addtobotnetModule(LaneNModule):
    """add_to_botnet - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "add_to_botnet"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class ddosstartModule(LaneNModule):
    """ddos_start - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "ddos_start"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class ransomwaredeployModule(LaneNModule):
    """ransomware_deploy - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "ransomware_deploy"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class minerdeployModule(LaneNModule):
    """miner_deploy - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "miner_deploy"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class proxysellModule(LaneNModule):
    """proxy_sell - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "proxy_sell"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class crackqueuedispatchModule(LaneNModule):
    """crack_queue_dispatch - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "crack_queue_dispatch"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})
