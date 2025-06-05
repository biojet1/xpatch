#!/usr/bin/env python3
from binascii import hexlify
import unittest
import subprocess
import hashlib
from pathlib import Path
import tempfile
import shutil
import sys
import xml.etree.ElementTree as ET


class TestXPatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create test files and directories"""
        cls.test_dir = Path(tempfile.mkdtemp(prefix="xpatch_test_"))
        print(f"\nTest directory: {cls.test_dir}")

        # Create test files
        cls.original_file = cls.test_dir / "original.bin"
        cls.patched_file = cls.test_dir / "patched.bin"
        cls.patch_file = cls.test_dir / "test_patch.xml"

        # Sample binary content: "Hello World!" (12 bytes)
        cls.original_content = b"Hello World!"
        cls.original_file.write_bytes(cls.original_content)

        # Expected patched content: "Goodbye World!" (still 12 bytes)
        cls.patched_content = b"GoodbyWorld!"

        # Create patch XML
        patch_xml = ET.Element(
            "patch", name="test_patch", md5sum=cls.get_md5(cls.original_file)
        )
        alter = ET.SubElement(
            patch_xml, "alter", id="test_alter", start="0", length="6"
        )
        ET.SubElement(alter, "from").text = hexlify(b"Hello ").decode()
        ET.SubElement(alter, "to").text = hexlify(b"Goodby").decode()
        cls.patch_file.write_bytes(ET.tostring(patch_xml))

        print(f"Created test files in {cls.test_dir}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test directory"""
        shutil.rmtree(cls.test_dir)
        print(f"\nCleaned up test directory: {cls.test_dir}")

    @classmethod
    def get_md5(cls, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        return hashlib.md5(file_path.read_bytes()).hexdigest()

    def run_xpatch(self, *args, expect_success=True):
        """Run xpatch command and return output"""
        cmd_args = ["python", "-m", "xpatch"] + [str(arg) for arg in args]
        print(f"\nExecuting: {' '.join(cmd_args)}")

        result = subprocess.run(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        print(f"Output:\n{result.stdout}")
        if expect_success:
            self.assertEqual(
                result.returncode, 0, f"Command failed with output:\n{result.stdout}"
            )
        else:
            self.assertNotEqual(result.returncode, 0, f"Command unexpectedly succeeded")
        return result.stdout

    # @unittest.skip("Enable to test basic patching")
    def test_basic_patching(self):
        """Test applying a simple patch"""
        # Copy original file to avoid modifying it
        test_file = self.test_dir / "test_file.bin"
        shutil.copy2(self.original_file, test_file)

        # Apply patch
        self.run_xpatch(self.patch_file, test_file)

        # Verify file was patched correctly
        self.assertEqual(test_file.read_bytes(), self.patched_content)

    # @unittest.skip("Enable to test dry run")
    def test_dry_run(self):
        """Test dry run doesn't modify file"""
        test_file = self.test_dir / "test_file_dry.bin"
        shutil.copy2(self.original_file, test_file)

        # Run with dry mode
        output = self.run_xpatch(self.patch_file, test_file, "-n")

        # Verify file wasn't modified
        self.assertEqual(test_file.read_bytes(), self.original_content)

        # Check dry run was detected in output
        # self.assertIn("(dry run)", output)

    # @unittest.skip("Enable to test unpatching")
    def test_unpatching(self):
        """Test unpatching reverts changes"""
        test_file = self.test_dir / "test_file_unpatch.bin"
        shutil.copy2(self.original_file, test_file)

        # First apply patch
        self.run_xpatch(self.patch_file, test_file)
        self.assertEqual(test_file.read_bytes(), self.patched_content)

        # Then unpatch
        self.run_xpatch(self.patch_file, test_file, "-u")

        # Should be back to original
        self.assertEqual(test_file.read_bytes(), self.original_content)

    # @unittest.skip("Enable to test MD5 verification")
    def test_md5_verification(self):
        """Test MD5 verification works"""
        test_file = self.test_dir / "test_file_md5.bin"
        shutil.copy2(self.original_file, test_file)

        # Should work with correct MD5
        self.run_xpatch(self.patch_file, test_file, "-m")

        # Modify file to break MD5
        test_file.write_bytes(b"Modified!!")

        # Should fail verification
        with self.assertRaises(AssertionError):
            self.run_xpatch(self.patch_file, test_file, "-m", expect_success=False)

    # @unittest.skip("Enable to test invalid patch")
    def test_invalid_patch(self):
        """Test handling of invalid patch data"""
        test_file = self.test_dir / "test_file_invalid.bin"
        shutil.copy2(self.original_file, test_file)

        # Create invalid patch (wrong 'from' data)
        invalid_patch = self.test_dir / "invalid_patch.xml"
        patch_xml = ET.Element("patch")
        alter = ET.SubElement(patch_xml, "alter", id="invalid", start="0", length="6")
        ET.SubElement(alter, "from").text = hexlify(b"WRONG ").decode()
        ET.SubElement(alter, "to").text = hexlify(b"Goodby").decode()
        invalid_patch.write_bytes(ET.tostring(patch_xml))

        # Should fail to apply
        with self.assertRaises(AssertionError):
            self.run_xpatch(invalid_patch, test_file, expect_success=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
