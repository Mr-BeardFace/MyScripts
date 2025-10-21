# xp_jobshell

Execute commands on MSSQL servers using SQL Server Agent Jobs - an alternative to `xp_cmdshell` that doesn't require it to be enabled.

## Overview

This tool creates temporary SQL Server Agent jobs with PowerShell job steps to execute commands and retrieve output via temporary tables. All artifacts (jobs and tables) are automatically cleaned up after execution.

## Features

- Execute PowerShell commands without `xp_cmdshell`
- Automatic cleanup of jobs and tables
- Verification of successful cleanup
- Works with SQL Server 2012+
- Only requires SQL Server Agent to be running

## Requirements

- Python 3
- `pymssql` library
- SQL Server Agent service running on target
- Permissions to create/execute jobs (typically requires `sysadmin` or specific Agent permissions)

## Installation
```bash
pip install pymssql
```

## Usage
```bash
python xp_jobshell.py -s  -u  -p  -d  -c 
```

### Parameters

- `-s, --server`: MSSQL Server (IP or hostname)
- `-u, --username`: Username for authentication
- `-p, --password`: Password for authentication
- `-d, --database`: Database to use (default: master)
- `-c, --command`: PowerShell command to execute

### Examples

**Basic command execution:**
```bash
python xp_jobshell.py -s 10.0.0.50 -u sa -p Password123 -c "whoami"
```

**Get running processes:**
```bash
python xp_jobshell.py -s 10.0.0.50 -u sa -p Password123 -c "Get-Process"
```

**File operations:**
```bash
python xp_jobshell.py -s 10.0.0.50:60000 -u sa -p Password123 -c "Get-ChildItem C:\\"
```

**Domain information:**
```bash
python xp_jobshell.py -s sqlserver.domain.com -u 'DOMAIN\user' -p Pass123 -c "Get-ADUser -Filter *"
```

## How It Works

1. Creates a temporary table with a random name
2. Creates a SQL Server Agent job with a PowerShell step
3. The PowerShell script executes the command and writes output to the temp table
4. Polls job history for completion status
5. Retrieves output from the temp table
6. Deletes the job and table
7. Verifies cleanup was successful

## Advantages Over xp_cmdshell

- Doesn't require `xp_cmdshell` to be enabled
- Uses PowerShell subsystem for cleaner execution
- Native PowerShell integration (no command-line escaping issues)
- Job-based execution can be harder to detect

## Limitations

- Requires SQL Server Agent service to be running
- Requires permissions to create and execute jobs
- Slightly slower than `xp_cmdshell` due to job creation overhead
- Jobs run under the SQL Server Agent service account context

## Security Considerations

This tool is intended for authorized penetration testing and red team operations only. Unauthorized access to systems is illegal.

**Detection:**
- Creates temporary jobs in `msdb.dbo.sysjobs`
- Creates temporary tables in the target database
- Job execution appears in SQL Server Agent logs
- PowerShell execution may trigger EDR/AV

## Troubleshooting

**"Job failed" errors:**
- Check SQL Server Agent service is running
- Verify account has job execution permissions
- Review error message in output for details

**Connection errors:**
- Ensure port 1433 is accessible
- Verify credentials are correct
- Check if SQL Server allows remote connections

**Empty output:**
- Command may not have produced output
- Check job history for execution errors
- Verify PowerShell command syntax

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is provided for educational and authorized testing purposes only. Users are responsible for complying with applicable laws and regulations.
