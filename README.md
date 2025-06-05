# **XPatch - XML-Based Binary Patching Tool**

**XPatch** is a command-line tool for applying binary patches to files using XML-based patch definitions. It supports patching, unpatching (reverting changes), and file integrity verification via MD5 checksums.

## **Features**

✅ **XML Patch Definitions** – Define binary patches in XML for precise file modifications.  
✅ **Dry Run Mode** – Test patches before applying them.  
✅ **Unpatch Support** – Revert applied patches when needed.  
✅ **MD5 Verification** – Ensure file integrity before and after patching.

---

## **Usage**

### **Basic Patching**

```bash
xpatch PATCH_FILE.xml TARGET_FILE [OPTIONS]
```

### **Options**

| Flag            | Description                                  |
| --------------- | -------------------------------------------- |
| `-n, --dry-run` | Test patch without modifying the file        |
| `-u`            | Unpatch (revert changes) instead of patching |
| `-v`            | Verbose output (show detailed logs)          |
| `-m`            | Verify MD5 checksum before patching          |

---

## **Patch XML Format**

Example patch file (`example.xml`):

```xml
<patch name="example_patch" md5sum="d41d8cd98f00b204e9800998ecf8427e">
  <alter id="patch1" start="0x100" length="16">
    <from encoding="hex">48656c6c6f20576f726c6421</from> <!-- "Hello World!" -->
    <to encoding="hex">476f6f646279652021</to>         <!-- "Goodbye !" -->
  </alter>
</patch>
```

### **XML Structure**

- **`<patch>`** (Root element)
  - `name`: Patch identifier (optional)
  - `md5sum`: Expected MD5 of the target file (optional, used with `-m`)
- **`<alter>`** (Patch operation)
  - `id`: Unique identifier for the patch
  - `start`: Byte offset where the patch starts (hex or decimal)
  - `length`: Number of bytes to replace (optional, defaults to `<from>` length)
- **`<from>`** (Original data)
  - `encoding="hex"` (default) or `encoding="text"`
- **`<to>`** (New data)
  - Must be ≤ length of `<from>`

---

## **Examples**

### **1. Apply a Patch**

```bash
xpatch example.xml target.bin -v -m
```

- Verifies `target.bin` matches the expected MD5 (`md5sum` in XML).
- Applies changes defined in `example.xml`.
- Logs verbose output.

### **2. Dry Run (Test Patch Without Applying)**

```bash
xpatch example.xml target.bin -n
```

- Checks if the patch is applicable without modifying the file.

### **3. Unpatch (Revert Changes)**

```bash
xpatch example.xml target.bin -u
```

- Reverts the changes made by `example.xml`.

---

**XPatch** – The flexible binary patching tool. 🔧🔗
