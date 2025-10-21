# xp_jobshell

Execute commands on MSSQL servers using SQL Server Agent Jobs - an alternative to `xp_cmdshell` that doesn't require it to be enabled.

## Overview

This tool creates temporary SQL Server Agent jobs with PowerShell job steps to execute commands and retrieve output via temporary tables. All artifacts (jobs and tables) are automatically cleaned up after execution.

## Features

- Execute PowerShell commands without `xp_cmdshell`
- **Token impersonation** - steal tokens from running processes to execute commands as other users
- Automatic cleanup of jobs and tables
- Verification of successful cleanup
- Works with SQL Server 2012+
- Only requires SQL Server Agent to be running

## Requirements

- Python 3
- `pymssql` library
- SQL Server Agent service running on target
- Permissions to create/execute jobs (typically requires `sysadmin` or specific Agent permissions)
- For token theft: Local administrator privileges on the SQL Server host

## Installation
```bash
pip install pymssql
```

## Usage

### Basic Command Execution
```bash
python xp_jobshell.py -s <server> -u <username> -p <password> -d <database> -c <command>
```

### Token Impersonation
```bash
python xp_jobshell.py -s <server> -u <username> -p <password> --pid <process_id> -c <command>
```

### Parameters

- `-s, --server`: MSSQL Server (IP or hostname)
- `-u, --username`: Username for authentication
- `-p, --password`: Password for authentication
- `-d, --database`: Database to use (default: master)
- `-c, --command`: Command to execute** (PowerShell cmdlets only when using impersonation)
- `--pid`: Process ID to steal token from (optional, requires local admin on SQL host)
- `--port`: SQL Server port (default: 1433)

## Examples

**Basic command execution:**
```bash
python xp_jobshell.py -s 10.0.0.50 -u sa -p Password123 -c "Get-Process"
```

**Get current identity:**
```bash
python xp_jobshell.py -s 10.0.0.50 -u sa -p Password123 -c "[System.Security.Principal.WindowsIdentity]::GetCurrent().Name"
```

**Token impersonation - find target process:**
```bash
python xp_jobshell.py -s sqlserver -u sa -p pass -c "Get-Process -IncludeUserName | Where-Object { \$_.UserName -like '*admin*' } | Select-Object Id, ProcessName, UserName"
```

**Token impersonation - execute as stolen identity:**
```bash
python xp_jobshell.py -s sqlserver -u sa -p pass --pid 1234 -c "Get-ChildItem C:\Users\Administrator"
```

**Active Directory queries with stolen token:**
```bash
python xp_jobshell.py -s sqlserver -u sa -p pass --pid 1234 -c "Get-ADUser username"
```

## Token Impersonation

### How It Works

When using the `--pid` flag, the tool:
1. Opens the target process and extracts its access token
2. Duplicates the token for impersonation
3. Executes your PowerShell command under the stolen identity
4. Returns output and cleans up

### Important Limitations

**PowerShell Cmdlets Only:**
- ✓ Works: `Get-Process`, `Get-ChildItem`, `Get-ADUser`, `[System.Security.Principal.WindowsIdentity]::GetCurrent().Name`
- ✗ Doesn't work: `whoami.exe`, `net.exe`, `cmd.exe` (external executables spawn new processes that lose impersonation)

**Impersonation Level:**
- The stolen token provides **local access** as the target user
- **Network authentication** may be limited depending on:
  - Whether the account has "Cannot be delegated" flag set
  - Token impersonation level (Impersonation vs Delegation)
- Local file system access and local operations work fully
- Domain operations may require the account to allow delegation

**What Works:**
- Local file/registry access as the impersonated user
- PowerShell cmdlets and .NET methods
- Some AD queries (if token has appropriate level)

**What May Not Work:**
- Network authentication to remote systems
- Domain operations if account is marked "sensitive and cannot be delegated"
- External executables (use PowerShell equivalents)

### Finding Processes to Impersonate
```bash
# List all processes with usernames
python xp_jobshell.py -s server -u sa -p pass -c "Get-Process -IncludeUserName | Select-Object Id, ProcessName, UserName"

# Find privileged accounts
python xp_jobshell.py -s server -u sa -p pass -c "Get-Process -IncludeUserName | Where-Object { \$_.UserName -like '*admin*' }"
```

## How It Works

1. Creates a temporary table with a random name
2. Creates a SQL Server Agent job with a PowerShell step
3. The PowerShell script executes the command (with optional token impersonation)
4. Output is written to the temporary table
5. Polls job history for completion status
6. Retrieves output from the temp table
7. Deletes the job and table
8. Verifies cleanup was successful

## Advantages Over xp_cmdshell

- Doesn't require `xp_cmdshell` to be enabled
- Uses PowerShell subsystem for cleaner execution
- Native PowerShell integration (no command-line escaping issues)
- Job-based execution can be harder to detect
- Token impersonation allows privilege escalation

## Limitations

- Requires SQL Server Agent service to be running
- Requires permissions to create and execute jobs
- Slightly slower than `xp_cmdshell` due to job creation overhead
- Jobs run under the SQL Server Agent service account context (unless using token impersonation)
- **Commands must be PowerShell cmdlets/scripts** - external executables don't work with impersonation

## Security Considerations

This tool is intended for authorized penetration testing and red team operations only. Unauthorized access to systems is illegal.

**Detection:**
- Creates temporary jobs in `msdb.dbo.sysjobs`
- Creates temporary tables in the target database
- Job execution appears in SQL Server Agent logs
- PowerShell execution may trigger EDR/AV
- Token impersonation may be logged in security events

## Troubleshooting

**"Job failed" errors:**
- Check SQL Server Agent service is running
- Verify account has job execution permissions
- Review error message in output for details

**Connection errors:**
- Ensure port 1433 (or custom port) is accessible
- Verify credentials are correct
- Check if SQL Server allows remote connections

**Empty output:**
- Command may not have produced output
- Check job history for execution errors
- Verify PowerShell command syntax

**Token impersonation failures:**
- Ensure you're running as local administrator on the SQL host
- Verify the target PID exists and is accessible
- Check that the command is a PowerShell cmdlet (not external .exe)
- Some accounts may have "Cannot be delegated" flag preventing full impersonation

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is provided for educational and authorized testing purposes only. Users are responsible for complying with applicable laws and regulations.
