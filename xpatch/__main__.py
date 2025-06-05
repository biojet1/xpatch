#!/usr/bin/env python3
import re
import hashlib
import sys
from typing import List, Dict, Any
from binascii import unhexlify, hexlify
from pathlib import Path
from xml.dom.minidom import parse
from .cliskel import Main, arg, flag

__version__ = "1.2.0"

srx = re.compile(r"\s+")


def say(*args, **kwargs):
    """Print to stderr"""
    print(*args, **kwargs, file=sys.stderr)


def file_md5_digest(fname: Path, chunksize: int = 65536) -> str:
    """Calculate MD5 hash of a file"""
    m = hashlib.md5()
    with fname.open("rb") as f:
        while True:
            blck = f.read(chunksize)
            if not blck:
                break
            m.update(blck)
    return m.hexdigest()


def merge_data(a: bytes, b: bytes) -> bytes:
    """Merge two byte sequences"""
    A = len(a)
    B = len(b)
    if B > A:
        return a + b[A:]
    return a


def check_md5(file: Path, expected_md5: str) -> bool:
    """Verify file MD5 hash"""
    actual_md5 = file_md5_digest(file)
    if actual_md5 == expected_md5:
        say(f"MD5: OK {expected_md5}")
        return True
    else:
        say(f"Error: Invalid MD5 {actual_md5} != {expected_md5}")
        return False


class XPatch(Main):
    """XML-based binary patching tool"""

    # Command options
    dry_run: bool = flag("-n", "--dry-run", help="Test only, don't actually patch")
    un_patch: bool = flag("-u", help="Unpatch instead of patch")
    # verbose: bool = flag("-v", help="Verbose output")
    verify: bool = flag("-m", help="Verify MD5 digest if provided")
    patch_file: Path = arg("PATCH_FILE", help="XML patch file")
    target_files: "list[Path]" = arg(
        "TARGET", nargs="+", help="Files to patch", type=Path
    )

    def patch_db(self, patfile: Path):
        """Parse patch XML file"""

        def data_of(cur, name: str) -> bytes:
            """Extract data from XML node"""
            cur = cur.getElementsByTagName(name).item(0)
            enc = cur.getAttribute("encoding")
            data = cur.firstChild.data
            if enc:
                data = data.encode(enc)
            else:
                data = unhexlify(srx.sub("", data).encode("ascii"))
            return data

        patches = []
        meta = {}
        node = parse(str(patfile)).documentElement
        meta["md5"] = node.getAttribute("md5sum")
        meta["name"] = node.getAttribute("name")

        for i, alter in enumerate(node.getElementsByTagName("alter"), 1):
            id = alter.getAttribute("id") or f"#{i}"
            start = int(alter.getAttribute("start"), 0)
            assert start >= 0

            data_from, data_to = data_of(alter, "from"), data_of(alter, "to")
            assert len(data_from) > 0 and len(data_to) > 0
            assert len(data_to) <= len(data_from)

            length = alter.getAttribute("length")
            if length:
                length = int(length, 0)
            else:
                end = alter.getAttribute("end")
                if end:
                    length = (int(end, 0) - start) + 1
                else:
                    length = len(data_from)
            assert length > 0
            assert len(data_from) <= length

            if self.un_patch:
                data_from, data_to = merge_data(data_to, data_from), data_from

            patches.append(
                {
                    "id": id,
                    "start": start,
                    "length": length,
                    "dataFrom": data_from,
                    "dataTo": data_to,
                    "use": 0,
                }
            )

        return meta, patches

    def apply_patch(self, patches: "List[Dict[str, Any]]", target: Path) -> None:
        """Apply patches to target file"""
        use = 0
        with target.open("rb") as f:
            for alter in patches:
                f.seek(alter["start"])
                data = f.read(alter["length"])

                alter["use"] = 0
                if len(data) != alter["length"]:
                    say(
                        f"Warning: Invalid length {len(data)} read for '{alter['id']}', expected {alter['length']}"
                    )
                elif alter["dataFrom"] == data[: len(alter["dataFrom"])]:
                    alter["use"] = 1
                    use += 1
                elif alter["dataTo"] == data[: len(alter["dataTo"])]:
                    say("Skipping:", alter["id"])
                else:
                    say("Invalid:", alter["id"], hexlify(data[:31]).decode())

        if use > 0:
            mode = "rb" if self.dry_run else "r+b"
            with target.open(mode) as f:
                for alter in patches:
                    if alter["use"]:
                        say("Applying:", alter["id"])
                        f.seek(alter["start"])
                        if not self.dry_run:
                            f.write(alter["dataTo"])

    def start(self):
        say(f"Patch: {self.patch_file}")
        meta, patches = self.patch_db(self.patch_file)

        for target in self.target_files:
            say(f"Source: {target}")

            # Verify MD5 if requested (only when patching, not unpatching)
            if not self.dry_run and not self.un_patch and self.verify and meta["md5"]:
                if not check_md5(target, meta["md5"]):
                    continue

            self.apply_patch(patches, (target))

            # Verify MD5 after unpatching if requested
            if not self.dry_run and self.un_patch and self.verify and meta["md5"]:
                check_md5(target, meta["md5"])


def main():
    """CLI entry point."""
    XPatch().main()


__name__ == "__main__" and main()
