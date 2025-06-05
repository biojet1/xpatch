#!/usr/bin/env python
import unittest
import os
import tempfile
import hashlib
import binascii
from xml.dom.minidom import parseString

# Import the functions from xpatch.py
from xpatch import FileMD5Digest, mergeData, patchDB, patch


class TestXpatch(unittest.TestCase):
    def setUp(self):
        # Create a temporary binary file for testing
        self.test_binary = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        self.test_binary.write(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")
        self.test_binary.close()

        # Create a mock XML patch file
        self.patch_xml = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        self.patch_xml.write(
            b"""<?xml version="1.0"?>
<patches md5sum="%s" name="test_patch">
  <alter id="test1" start="0x2" length="4">
    <from>020304</from>
    <to>FFEEFF</to>
  </alter>
</patches>"""
            % FileMD5Digest(self.test_binary.name).encode()
        )
        self.patch_xml.close()

    def tearDown(self):
        os.unlink(self.test_binary.name)
        os.unlink(self.patch_xml.name)

    def test_FileMD5Digest(self):
        """Test MD5 digest calculation."""
        md5 = FileMD5Digest(self.test_binary.name)
        expected_md5 = hashlib.md5(
            b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
        ).hexdigest()
        self.assertEqual(md5, expected_md5)

    def test_mergeData(self):
        """Test merging binary data."""
        result = mergeData(b"ABC", b"XYZ")
        self.assertEqual(result, b"ABC")
        result = mergeData(b"ABC", b"W")
        self.assertEqual(result, b"ABC")
        result = mergeData(b"ABC", b"WXYZ")
        self.assertEqual(result, b"ABCZ")

    def test_patchDB(self):
        """Test parsing the patch XML."""

        class MockContext:
            unPatch = False
            bVerbose = False

        meta, patches = patchDB(self.patch_xml.name, MockContext())
        self.assertEqual(meta["name"], "test_patch")
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["id"], "test1")
        self.assertEqual(patches[0]["start"], 2)
        self.assertEqual(patches[0]["length"], 4)
        self.assertEqual(patches[0]["dataFrom"], b"\x02\x03\x04")
        self.assertEqual(patches[0]["dataTo"], b"\xff\xee\xff")

    def test_patch_apply(self):
        """Test applying a patch."""

        class MockContext:
            unPatch = False
            bVerbose = False
            dryRun = False
            bVerify = False

        meta, patches = patchDB(self.patch_xml.name, MockContext())
        patch(patches, self.test_binary.name, MockContext())

        with open(self.test_binary.name, "rb") as f:
            patched_data = f.read()
        self.assertEqual(patched_data, b"\x00\x01\xff\xee\xff\x05\x06\x07\x08\x09")

    def test_patch_unapply(self):
        """Test reverting a patch."""

        class MockContext:
            unPatch = True
            bVerbose = False
            dryRun = False
            bVerify = False

        meta, patches = patchDB(self.patch_xml.name, MockContext())
        patch(patches, self.test_binary.name, MockContext())

        with open(self.test_binary.name, "rb") as f:
            unpatched_data = f.read()
        self.assertEqual(unpatched_data, b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")


if __name__ == "__main__":
    unittest.main()
