# Silent Harvester

A stealthy Windows credential extraction tool that bypasses modern EDR solutions by leveraging overlooked Windows APIs and legitimate backup/restore mechanisms.

## Credit

This tool is based on the technique described in the blog post **"Silent Harvest: Extracting Windows Secrets Under the Radar"** by **sud0ru** ([https://sud0ru.ghost.io/silent-harvest-extracting-windows-secrets-under-the-radar/](https://sud0ru.ghost.io/silent-harvest-extracting-windows-secrets-under-the-radar/)).

The core methodology uses:
- `NtOpenKeyEx` with `REG_OPTION_BACKUP_RESTORE` flag to bypass ACLs
- `RegQueryMultipleValuesW` (a rarely monitored API) to read registry values
- Direct memory access to avoid disk artifacts

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Requirements](#requirements)
- [Compilation](#compilation)
- [Usage](#usage)
- [Detection Evasion](#detection-evasion)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [Defensive Recommendations](#defensive-recommendations)
- [Legal Disclaimer](#legal-disclaimer)
- [Credits](#credits)

## How It Works

### Why It Bypasses EDR

1. **SeBackupPrivilege Instead of SYSTEM**: Runs as a regular administrator with SeBackupPrivilege enabled, not SYSTEM. This allows bypassing normal ACL checks on protected registry keys without requiring elevation to SYSTEM.

2. **Obscure API Usage**: Uses `RegQueryMultipleValuesW` instead of the commonly monitored `RegQueryValueExW`. EDR vendors focus on high-frequency APIs and have overlooked this rarer interface.

3. **No Intermediate Files**: Reads directly from registry memory using NTAPI paths (`\Registry\Machine\SAM\...`). Unlike traditional methods that use `reg save` or Volume Shadow Copy to create intermediate hive files, this tool extracts values directly from memory and only writes the final output files (bootkey, F.bin, V_*.bin).

4. **Legitimate Backup Semantics**: Uses Windows' own backup/restore mechanism (`REG_OPTION_BACKUP_RESTORE`) which is a legitimate administrative function, making it harder to flag as malicious.

## Features

- Extracts Windows SAM user account data (encrypted password hashes)
- Extracts bootkey from SYSTEM registry hive
- Extracts F value (domain key) from SAM
- No disk writes during extraction (only output files)
- Bypasses common EDR detection mechanisms (tested against MDR)

## Requirements

### SilentHarvest.exe (C#)
- Windows 7+ (tested on Windows 10/11/Server 2016+)
- Administrator privileges
- SeBackupPrivilege (usually granted to Administrators group)
- .NET Framework 4.0+ or compile as standalone

### decrypt_sam.py (Python)
- Python 3.6+
- `pycryptodome` library

## Compilation
```cmd
csc.exe /out:SilentHarvest.exe SilentHarvest.cs
```

## Usage

### Step 1: Run SilentHarvest on Target
```cmd
# On the target Windows machine (as Administrator)
SilentHarvest.exe
```

**Output files:**
- `bootkey.bin` / `bootkey.txt` - System bootkey (16 bytes)
- `F.bin` - SAM domain key
- `V_000001F4.bin`, `V_000001F5.bin`, etc. - User account data (one per user)

### Step 2: Exfiltrate Files

Transfer the following files to your analysis machine:
- `bootkey.bin` (or `bootkey.txt`)
- `F.bin`
- All `V_*.bin` files

### Step 3: Decrypt with Python
```bash
# Install dependencies
pip3 install pycryptodome

# Run decryption script
python3 decryptSAM.py
```

**Output format:**
```
Administrator:500:aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
```

## Detection Evasion

This tool is designed to evade detection by:

1. **No suspicious process execution** - Pure registry API calls
2. **No LSASS interaction** - Avoids heavily monitored process
3. **No intermediate hive files** - No `reg save`, no VSS creation, reads directly from memory
4. **Legitimate Windows APIs** - Uses documented backup/restore functions
5. **Direct registry access** - NTAPI calls to read values from memory, not disk

**Note:** While this technique bypasses many EDR solutions, it may still be detected by:
- Advanced behavior analytics
- SeBackupPrivilege usage monitoring
- Custom detection rules targeting registry access patterns
- File creation monitoring (output files are still written)

## Technical Details

### Registry Paths Used

- Bootkey: `\Registry\Machine\SYSTEM\CurrentControlSet\Control\Lsa\{JD,Skew1,GBG,Data}`
- SAM Users: `\Registry\Machine\SAM\SAM\Domains\Account\Users\{RID}`
- Domain Key: `\Registry\Machine\SAM\SAM\Domains\Account` (F value)

### Encryption Details

1. **Bootkey Construction**: Concatenate class names from JD+Skew1+GBG+Data, then apply permutation
2. **Hashed Bootkey**: RC4 decrypt of F[0x70:0x80] using MD5(bootkey + salt)
3. **Password Hash**: DES decrypt using RID-derived keys and hashed bootkey

### File Formats

- **bootkey.bin**: Raw 16-byte binary bootkey
- **F.bin**: SAM domain account data (contains encrypted hashed bootkey)
- **V_*.bin**: User account structure (contains encrypted NT/LM hashes and metadata)

## Defensive Recommendations

To detect this technique:

1. **Monitor SeBackupPrivilege usage** - Alert on non-standard processes enabling this privilege
2. **Registry access monitoring** - Monitor direct NTAPI registry access to `\Registry\Machine\SAM` and `\Registry\Machine\SECURITY`
3. **Behavioral analytics** - Flag unusual registry enumeration patterns
4. **Restrict SeBackupPrivilege** - Remove from non-essential administrator accounts
5. **Update detection rules** - Add `RegQueryMultipleValuesW` to API monitoring

## Legal Disclaimer

This tool is provided for **authorized security assessments and research purposes only**. 

- Only use on systems you own or have explicit written permission to test
- Unauthorized access to computer systems is illegal
- The authors are not responsible for misuse or damage caused by this tool

## Credits

- **Technique**: sud0ru - [https://sud0ru.ghost.io/silent-harvest-extracting-windows-secrets-under-the-radar/](https://sud0ru.ghost.io/silent-harvest-extracting-windows-secrets-under-the-radar/)
- **Implementation**: Based on research into Windows internal registry APIs and SAM encryption
- **Inspiration**: Mimikatz, Impacket secretsdump, and Windows internals research

## References

- [Silent Harvest Blog Post](https://sud0ru.ghost.io/silent-harvest-extracting-windows-secrets-under-the-radar/)
- [Microsoft Documentation: Backup and Restore](https://docs.microsoft.com/en-us/windows/win32/backup/backup-and-restore)
- [SAM Database Structure](https://www.insecurity.be/blog/2018/01/21/retrieving-ntlm-hashes-and-what-changed-technical-writeup/)
