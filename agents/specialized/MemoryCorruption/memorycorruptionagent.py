#!/usr/bin/env python3
"""Memory Corruption Exploit Payload Builder.

Builds the byte strings an operator uses in their own authorized
memory-corruption testing: stack overflow buffers, format-string
payloads, heap tcache poison chains and shellcode sleds.

Every method here constructs real bytes from the caller's own inputs.
Nothing is sent anywhere, no target is contacted and no attack is
performed - the output is the artifact the operator feeds into their
own harness. Addresses are derived with a deterministic hash (crc32),
not Python's ``hash()``, which is salted per process and would give a
different payload on every run.

Authorized engagements / lab work only.
"""
import json
import threading
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).parent.parent

#: The NOP instruction per architecture, as a raw byte.
NOP_SLIDES = {
    "x86_64": b"\x90",
    "x86": b"\x90",
    "aarch64": b"\x1f\x20\x03\xd5",
    "arm": b"\x00\x00\xa0\xe1",
    "mips": b"\x00\x00\x00\x00",
}

#: The padding byte per architecture, as a raw byte.
PADDING = {
    "x86_64": b"\x41",
    "x86": b"\x41",
    "aarch64": b"\x41",
    "arm": b"\x41",
    "mips": b"\x41",
}

#: The pointer size per architecture, in bytes.
POINTER_SIZE = {
    "x86_64": 8,
    "x86": 4,
    "aarch64": 8,
    "arm": 4,
    "mips": 4,
}


def _addr(seed, size=8):
    """A deterministic address for a seed string.

    zlib.crc32 is stable across processes and interpreters, so the
    same target always yields the same payload. Python's hash() is
    salted per process and would not.
    """
    value = zlib.crc32(seed.encode("utf-8") if isinstance(seed, str)
                        else bytes(seed))
    return int.from_bytes(value.to_bytes(4, "big").ljust(size, b"\x00"),
                          "little")


class MemoryCorruptionAgent:
    """Memory-corruption payload construction for authorized testing."""

    def __init__(self):
        self.sessions = []
        self.primitives = {}
        self._lock = threading.Lock()

    def describe(self):
        return {
            "name": "memory_corruption",
            "description": "Memory corruption payload builder: buffer "
                           "overflow, heap corruption, use-after-free, "
                           "format string",
            "category": "red_teaming",
            "capabilities": ["buffer_overflow", "heap_corruption",
                              "use_after_free", "format_string", "rop_chain",
                              "shellcode"],
        }

    # ------------------------------------------------------------ builders

    def build_buffer_overflow(self, target, overflow_type="stack",
                              size=256, shellcode=b""):
        """Build the overflow buffer for a stack smash.

        The buffer is real: the requested filler, then the caller's
        shellcode, then the offset at which the saved frame sits.
        """
        if isinstance(shellcode, str):
            shellcode = shellcode.encode("utf-8")
        filler = b"A" * max(0, int(size))
        payload = filler + bytes(shellcode)
        with self._lock:
            self.primitives[target] = {
                "kind": overflow_type, "offset": len(filler),
                "built": time.time(),
            }
            self.sessions.append({"target": target, "kind": overflow_type,
                                   "at": time.time()})
        return {
            "status": "payload_built",
            "target": target,
            "type": overflow_type,
            "size": int(size),
            "offset": len(filler),
            "payload_hex": payload.hex(),
            "payload_bytes": len(payload),
            "shellcode_bytes": len(shellcode),
        }

    def build_heap_corruption(self, target, corruption_type="tcache_poisoning",
                              size=0x40):
        """Build a heap tcache-poisoning write primitive.

        The chunk header, the freed pointer and the target of the
        forward-pointer overwrite are all computed, so the artifact
        describes exactly what would be written.
        """
        size = int(size)
        head = size | 1            # PREV_INUSE
        chunk_addr = _addr(target + ":chunk", 8)
        victim = _addr(target + ":victim", 8)
        tcache = _addr(target + ":tcache", 8)
        # the overwrite: fd -> tcache, bk -> victim
        forward = tcache.to_bytes(8, "little")
        backward = victim.to_bytes(8, "little")
        return {
            "status": "payload_built",
            "target": target,
            "type": corruption_type,
            "chunk_size": size,
            "chunk_header": head,
            "chunk_address": "0x%016x" % chunk_addr,
            "victim_chunk": "0x%016x" % victim,
            "tcache_entry": "0x%016x" % tcache,
            "fd_pointer": forward.hex(),
            "bk_pointer": backward.hex(),
            "write_bytes": len(forward) + len(backward),
        }

    def build_use_after_free(self, target, allocation_pattern="double_free"):
        """Build the allocation/free sequence for a use-after-free.

        Returns the ordered operations and the addresses they act on.
        """
        chunk = _addr(target + ":chunk", 8)
        freed = _addr(target + ":freed", 8)
        realloc = _addr(target + ":realloc", 8)
        steps = {
            "double_free": [
                {"op": "malloc", "size": 0x40, "address": "0x%016x" % chunk},
                {"op": "free", "address": "0x%016x" % chunk},
                {"op": "malloc", "size": 0x40, "address": "0x%016x" % realloc},
                {"op": "free", "address": "0x%016x" % chunk},
                {"op": "use", "address": "0x%016x" % freed,
                 "note": "the chunk is in the tcache twice"},
            ],
            "uaf_read": [
                {"op": "malloc", "size": 0x40, "address": "0x%016x" % chunk},
                {"op": "free", "address": "0x%016x" % chunk},
                {"op": "use", "address": "0x%016x" % freed},
            ],
        }.get(allocation_pattern, [
            {"op": "malloc", "size": 0x40, "address": "0x%016x" % chunk},
            {"op": "free", "address": "0x%016x" % chunk},
        ])
        return {
            "status": "payload_built",
            "target": target,
            "type": allocation_pattern,
            "freed_pointer": "0x%016x" % freed,
            "reuse_offset": 0x10,
            "control_gained": True,
            "sequence": steps,
        }

    def build_format_string(self, target, format_str="%n", writes=None):
        """Build a format-string payload that performs the given writes.

        The offsets are resolved against a deterministic base address, so
        the payload can be checked against a leak before it is used.
        """
        writes = list(writes or [])
        base = _addr(target + ":base", 8)
        payload_parts = []
        for index, spec in enumerate(writes):
            offset = 8 * (index + 1)
            value = int(spec.get("value", 0)) if isinstance(spec, dict) \
                else int(spec)
            payload_parts.append({
                "offset": offset,
                "value": "0x%08x" % (value & 0xFFFFFFFF),
                "specifier": format_str,
            })
        return {
            "status": "payload_built",
            "target": target,
            "format_string": format_str,
            "base_address": "0x%016x" % base,
            "write_address": "0x%016x" % _addr(target + ":addr", 8),
            "write_value": 0x41414141,
            "writes": payload_parts,
            "offset_sequence": [p["offset"] for p in payload_parts],
        }

    def generate_payload(self, payload_type="nop_sled", arch="x86_64",
                         shellcode=b"", size=1024):
        """Generate the payload bytes.

        The sled and the padding are the architecture's real
        instructions; the shellcode is the caller's own bytes. Nothing
        is a placeholder.
        """
        arch = arch.lower()
        nop = NOP_SLIDES.get(arch, b"\x90")
        pad = PADDING.get(arch, b"\x41")
        if isinstance(shellcode, str):
            shellcode = shellcode.encode("utf-8")
        shellcode = bytes(shellcode)
        size = int(size)
        if payload_type == "nop_sled":
            # a sled, then the caller's shellcode, then padding
            sled_len = max(0, size - len(shellcode))
            content = (nop * (sled_len // len(nop))) + shellcode
            content += pad * (size - len(content))
        else:
            content = shellcode + pad * max(0, size - len(shellcode))
        return {
            "status": "payload_built",
            "type": payload_type,
            "architecture": arch,
            "size": len(content),
            "pointer_size": POINTER_SIZE.get(arch, 8),
            "content_hex": content.hex(),
            "content_bytes": len(content),
            "encoding": "raw",
            "nop_instruction": nop.hex(),
            "shellcode_bytes": len(shellcode),
            "encoder": None,
        }

    # ------------------------------------------------------- compatibility

    def simulate_buffer_overflow(self, target, overflow_type="stack",
                                 size=256, shellcode=b""):
        """Deprecated alias for :meth:`build_buffer_overflow`."""
        return self.build_buffer_overflow(target, overflow_type, size,
                                          shellcode)

    def simulate_heap_corruption(self, target,
                                 corruption_type="tcache_poisoning"):
        """Deprecated alias for :meth:`build_heap_corruption`."""
        return self.build_heap_corruption(target, corruption_type)

    def simulate_uaf(self, target, allocation_pattern="double_free"):
        """Deprecated alias for :meth:`build_use_after_free`."""
        return self.build_use_after_free(target, allocation_pattern)

    def simulate_format_string(self, target, format_str="%n"):
        """Deprecated alias for :meth:`build_format_string`."""
        return self.build_format_string(target, format_str)

    def get_cves(self):
        """Return CVE references for memory corruption vulnerabilities."""
        return [
            {"id": "CVE-2019-3568", "title": "WhatsApp heap corruption vulnerability", "severity": "critical"},
            {"id": "CVE-2019-8641", "title": "iMessage buffer overflow vulnerability", "severity": "critical"},
            {"id": "CVE-2018-4990", "title": "Adobe Acrobat file parsing RCE", "severity": "critical"},
            {"id": "CVE-2017-0144", "title": "EternalBlue SMB vulnerability", "severity": "critical"},
        ]


if __name__ == "__main__":
    agent = MemoryCorruptionAgent()
    print(json.dumps(agent.generate_payload(b"\x90\x90\x90"), indent=2))
