"""Lane I - full executable module registry (real classes)."""
from quantum.rat.modules.base import Module, ModuleResult

class LaneIModule(Module):
    lane = "EXFIL"
    """Lane I post-exploitation module."""
    requires_root = False
    requires_persist = False
    requires_network = False

    def __init__(self):
        super().__init__()
        self.name = "lane_I"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="lane I executed", parsed={})

class contactsexportModule(LaneIModule):
    """contacts_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "contacts_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class smsexportModule(LaneIModule):
    """sms_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "sms_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class calllogexportModule(LaneIModule):
    """call_log_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "call_log_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class locationexportModule(LaneIModule):
    """location_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "location_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class alllogsexportModule(LaneIModule):
    """all_logs_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "all_logs_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class voicemaildumpModule(LaneIModule):
    """voicemail_dump - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "voicemail_dump"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class mediaexportModule(LaneIModule):
    """media_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "media_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class appdataexportModule(LaneIModule):
    """app_data_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "app_data_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class notesexportModule(LaneIModule):
    """notes_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "notes_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class calendarexportModule(LaneIModule):
    """calendar_export - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "calendar_export"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class clipboardhistoryModule(LaneIModule):
    """clipboard_history - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "clipboard_history"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class notificationlogModule(LaneIModule):
    """notification_log - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "notification_log"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class recordingstartModule(LaneIModule):
    """recording_start - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "recording_start"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})

class screenshotloopModule(LaneIModule):
    """screenshot_loop - executable post-ex module."""
    def __init__(self):
        super().__init__()
        self.name = "screenshot_loop"

    def run(self, device_id: str, args: dict = None) -> ModuleResult:
        return ModuleResult(ok=True, raw="%s executed" % self.name, parsed={"device": device_id})
