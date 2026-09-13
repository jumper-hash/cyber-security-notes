#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse


SECLISTS = Path("/usr/share/seclists")

SUBDOMAIN_WORDLIST = (
    SECLISTS / "Discovery/DNS/subdomains-top1million-20000.txt"
)

WEB_WORDLIST = (
    SECLISTS / "Discovery/Web-Content/raft-medium-directories.txt"
)

HOSTS_FILE = Path("/etc/hosts")

HTB_START = "###HTB"
HTB_END = "###END_HTB"

HTTP_PORTS = {
    "80",
    "443",
    "8000",
    "8008",
    "8080",
    "8081",
    "8443",
    "8888",
}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        return None


OPENER = urllib.request.build_opener(
    NoRedirectHandler
)


def print_section(title):
    print()
    print("=" * 70)
    print(f"[+] {title}")
    print("=" * 70)


def run_command(command, output_file=None):
    print()
    print(f"[>] Command: {' '.join(command)}")

    if output_file:
        print(f"[>] Output : {output_file}")

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    except FileNotFoundError:
        print(
            f"[!] Command not found: {command[0]}"
        )
        return 127, ""

    except KeyboardInterrupt:
        print()
        print(
            "[!] Command interrupted by user."
        )
        return 130, ""

    if output_file:
        Path(output_file).write_text(
            result.stdout,
            encoding="utf-8",
        )

    print(
        f"[<] Exit code: {result.returncode}"
    )

    return (
        result.returncode,
        result.stdout,
    )


def parse_open_ports(nmap_output):
    ports = []

    for line in nmap_output.splitlines():
        match = re.match(
            r"^\s*(\d+)/tcp\s+open\s+",
            line,
        )

        if match:
            ports.append(
                match.group(1)
            )

    return sorted(
        set(ports),
        key=int,
    )


def detect_http_ports(open_ports):
    return [
        port
        for port in open_ports
        if port in HTTP_PORTS
    ]


def http_request(url, timeout=8):
    print(
        f"[>] HTTP GET without redirect: {url}"
    )

    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "HTB-Recon/1.0",
        },
    )

    try:
        response = OPENER.open(
            request,
            timeout=timeout,
        )

        return (
            response.geturl(),
            response.status,
            response.headers,
            response.read(),
        )

    except urllib.error.HTTPError as exc:
        location = exc.headers.get(
            "Location"
        )

        return (
            url,
            exc.code,
            exc.headers,
            exc.read(),
        )

    except urllib.error.URLError as exc:
        print(
            f"[!] HTTP error: {exc}"
        )
        return (
            None,
            None,
            None,
            None,
        )

    except Exception as exc:
        print(
            f"[!] HTTP request failed: {exc}"
        )
        return (
            None,
            None,
            None,
            None,
        )


def extract_hostname(url):
    if not url:
        return None

    try:
        parsed = urlparse(url)

        if parsed.hostname:
            return parsed.hostname.lower()

    except Exception:
        pass

    match = re.search(
        r"https?://([^/:]+)",
        url,
    )

    if match:
        return match.group(1).lower()

    return None


def get_htb_section(lines):
    try:
        start = lines.index(
            HTB_START
        )

        end = lines.index(
            HTB_END,
            start + 1,
        )

        return (
            start,
            end,
        )

    except ValueError:
        return (
            None,
            None,
        )


def update_hosts_file(
    ip,
    hostnames,
):
    if not hostnames:
        return False

    hostnames = sorted(
        {
            hostname.strip().lower()
            for hostname in hostnames
            if hostname.strip()
        }
    )

    if not hostnames:
        return False

    print(
        "[>] Updating /etc/hosts:"
    )

    print(
        f"    {ip}\t{' '.join(hostnames)}"
    )

    try:
        content = HOSTS_FILE.read_text(
            encoding="utf-8",
        )

    except PermissionError:
        print(
            "[!] Cannot read /etc/hosts."
        )

        print(
            "[!] Run the script with sudo."
        )

        return False

    lines = content.splitlines()

    start, end = get_htb_section(
        lines
    )

    if start is None:
        print(
            "[!] Could not find "
            "###HTB / ###END_HTB markers."
        )
        return False

    # Comment all active HTB entries.
    commented = 0

    for i in range(
        start + 1,
        end,
    ):
        stripped = lines[i].strip()

        if (
            stripped
            and not stripped.startswith("#")
        ):
            lines[i] = "#" + lines[i]
            commented += 1

    if commented:
        print(
            f"[+] Commented "
            f"{commented} active HTB entries."
        )

    # Remove an existing active entry
    # for this IP.
    start, end = get_htb_section(
        lines
    )

    new_lines = []

    for i, line in enumerate(lines):

        if start < i < end:

            stripped = line.strip()

            if (
                stripped
                and not stripped.startswith("#")
            ):

                parts = stripped.split()

                if parts and parts[0] == ip:
                    continue

        new_lines.append(line)

    lines = new_lines

    start, end = get_htb_section(
        lines
    )

    entry = (
        f"{ip}\t"
        f"{' '.join(hostnames)}"
    )

    # Last line before ###END_HTB.
    lines.insert(
        end,
        entry,
    )

    try:
        HOSTS_FILE.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    except PermissionError:
        print(
            "[!] Cannot write /etc/hosts."
        )

        print(
            "[!] Run the script with sudo."
        )

        return False

    print(
        "[+] /etc/hosts updated."
    )

    return True


def parse_ffuf_json(
    json_file,
    base_domain,
):
    discovered = set()

    try:
        data = json.loads(
            Path(json_file).read_text(
                encoding="utf-8"
            )
        )

    except FileNotFoundError:
        return discovered

    except json.JSONDecodeError as exc:
        print(
            f"[!] Cannot parse ffuf JSON: "
            f"{exc}"
        )
        return discovered

    results = data.get(
        "results",
        [],
    )

    suffix = (
        f".{base_domain.lower()}"
    )

    for result in results:

        host = result.get(
            "host"
        )

        if not host:
            continue

        host = host.strip().lower()

        if host.endswith(
            suffix
        ):
            discovered.add(
                host
            )

    return discovered


def main():
    parser = argparse.ArgumentParser(
        description=(
            "HTB recon automation: "
            "Nmap + redirect detection + "
            "VHost enumeration + endpoint fuzzing"
        )
    )

    parser.add_argument(
        "ip",
        help="Target IPv4 address",
    )

    parser.add_argument(
        "output",
        nargs="?",
        default=".",
        help="Output directory (default: .)",
    )

    args = parser.parse_args()

    ip = args.ip

    output_dir = (
        Path(args.output)
        .expanduser()
        .resolve()
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    nmap_full = (
        output_dir
        / "nmap-full.txt"
    )

    nmap_services = (
        output_dir
        / "nmap-services.txt"
    )

    redirects_file = (
        output_dir
        / "redirects.txt"
    )

    subdomains_file = (
        output_dir
        / "subdomains.txt"
    )

    subfinder_file = (
        output_dir
        / "subfinder.txt"
    )

    vhosts_file = (
        output_dir
        / "ffuf-vhosts.txt"
    )

    vhosts_json = (
        output_dir
        / "ffuf-vhosts.json"
    )

    directories_file = (
        output_dir
        / "ffuf-directories.txt"
    )

    # =========================================================
    # Header
    # =========================================================

    print()
    print("=" * 70)
    print(" HTB RECON")
    print("=" * 70)

    print(
        f"[+] Target : {ip}"
    )

    print(
        f"[+] Output : {output_dir}"
    )

    print(
        f"[+] SecLists: {SECLISTS}"
    )

    print("=" * 70)

    # =========================================================
    # 1. Full TCP scan
    # =========================================================

    print_section(
        "1/9 - Full TCP port scan"
    )

    rc, full_output = run_command(
        [
            "nmap",
            "-sS",
            "-p-",
            "--min-rate",
            "1000",
            "-T4",
            ip,
        ],
        nmap_full,
    )

    if rc == 130:
        print(
            "[!] Recon interrupted."
        )
        return 130

    open_ports = parse_open_ports(
        full_output
    )

    if not open_ports:
        print(
            "[!] No open TCP ports found."
        )
        return 1

    print()
    print(
        "[+] Open TCP ports:"
    )

    for port in open_ports:
        print(
            f"    - {port}"
        )

    # =========================================================
    # 2. Service/version detection
    # =========================================================

    print_section(
        "2/9 - Service and version detection"
    )

    rc, _ = run_command(
        [
            "nmap",
            "-sC",
            "-sV",
            "-p",
            ",".join(open_ports),
            ip,
        ],
        nmap_services,
    )

    if rc == 130:
        print(
            "[!] Recon interrupted."
        )
        return 130

    # =========================================================
    # 3. HTTP detection
    # =========================================================

    print_section(
        "3/9 - HTTP service detection"
    )

    http_ports = detect_http_ports(
        open_ports
    )

    if not http_ports:
        print(
            "[+] No common HTTP/HTTPS ports found."
        )
        return 0

    for port in http_ports:

        scheme = (
            "https"
            if port == "443"
            else "http"
        )

        print(
            f"[+] HTTP service: "
            f"{scheme}://{ip}:{port}"
        )

    # =========================================================
    # 4. Redirect detection
    # =========================================================

    print_section(
        "4/9 - HTTP redirect detection"
    )

    discovered_hosts = set()

    with redirects_file.open(
        "w",
        encoding="utf-8",
    ) as rf:

        for port in http_ports:

            scheme = (
                "https"
                if port == "443"
                else "http"
            )

            url = (
                f"{scheme}://{ip}/"
            )

            print()
            print(
                f"[+] Checking {url}"
            )

            final_url, status, headers, _ = (
                http_request(url)
            )

            if not headers:

                print(
                    "[-] No HTTP response."
                )

                rf.write(
                    f"{url} -> "
                    "no response\n"
                )

                continue

            location = headers.get(
                "Location"
            )

            if location:

                redirect_url = urljoin(
                    url,
                    location,
                )

                print(
                    "[+] Redirect found:"
                )

                print(
                    f"    {redirect_url}"
                )

                rf.write(
                    f"{url} -> "
                    f"{redirect_url}\n"
                )

                hostname = (
                    extract_hostname(
                        redirect_url
                    )
                )

                if hostname:

                    print(
                        "[+] Hostname discovered:"
                    )

                    print(
                        f"    {hostname}"
                    )

                    discovered_hosts.add(
                        hostname
                    )

            else:

                print(
                    f"[-] No redirect "
                    f"(HTTP {status})"
                )

                rf.write(
                    f"{url} -> "
                    f"no redirect "
                    f"(HTTP {status})\n"
                )

    # =========================================================
    # 5. /etc/hosts
    # =========================================================

    print_section(
        "5/9 - Updating /etc/hosts"
    )

    if discovered_hosts:

        update_hosts_file(
            ip,
            discovered_hosts,
        )

    else:

        print(
            "[-] No hostname discovered."
        )

    # =========================================================
    # 6. Target selection
    # =========================================================

    print_section(
        "6/9 - Selecting web target"
    )

    if discovered_hosts:

        target_domain = sorted(
            discovered_hosts
        )[0]

        print(
            f"[+] Target domain: "
            f"{target_domain}"
        )

    else:

        target_domain = None

        print(
            "[+] Using IP as web target."
        )

    # =========================================================
    # 7. Scheme
    # =========================================================

    print_section(
        "7/9 - Selecting HTTP scheme"
    )

    if (
        "443" in http_ports
        and "80" not in http_ports
    ):
        scheme = "https"
    else:
        scheme = "http"

    print(
        f"[+] Scheme: {scheme}"
    )

    if target_domain:

        base_url = (
            f"{scheme}://"
            f"{target_domain}"
        )

    else:

        base_url = (
            f"{scheme}://"
            f"{ip}"
        )

    print(
        f"[+] Base URL: "
        f"{base_url}"
    )

    # =========================================================
    # 8. VHost enumeration
    # =========================================================

    print_section(
        "8/9 - VHost / subdomain enumeration"
    )

    found_subdomains = set(
        discovered_hosts
    )

    if not target_domain:

        print(
            "[-] Skipping VHost enumeration."
        )

        subdomains_file.write_text(
            "",
            encoding="utf-8",
        )

    else:

        if (
            not SUBDOMAIN_WORDLIST.exists()
        ):

            print(
                "[!] Missing wordlist:"
            )

            print(
                f"    {SUBDOMAIN_WORDLIST}"
            )

        else:

            print(
                "[+] Starting ffuf VHost fuzzing..."
            )

            rc, _ = run_command(
                [
                    "ffuf",
                    "-w",
                    str(
                        SUBDOMAIN_WORDLIST
                    ),
                    "-u",
                    f"{scheme}://"
                    f"{target_domain}/",
                    "-H",
                    f"Host: FUZZ."
                    f"{target_domain}",
                    "-mc",
                    "200,204,301,302,307,401,403",
                    "-ac",
                    "-of",
                    "json",
                    "-o",
                    str(vhosts_json),
                ],
                vhosts_file,
            )

            if rc == 130:
                print(
                    "[!] VHost fuzzing interrupted."
                )

            ffuf_hosts = (
                parse_ffuf_json(
                    vhosts_json,
                    target_domain,
                )
            )

            if ffuf_hosts:

                print(
                    "[+] Valid VHosts found:"
                )

                for hostname in sorted(
                    ffuf_hosts
                ):
                    print(
                        f"    - {hostname}"
                    )

                found_subdomains.update(
                    ffuf_hosts
                )

            else:

                print(
                    "[-] No valid VHosts found."
                )

        # -----------------------------------------------------
        # subfinder
        # -----------------------------------------------------

        print()
        print(
            "[+] Running subfinder..."
        )

        rc, subfinder_output = (
            run_command(
                [
                    "subfinder",
                    "-d",
                    target_domain,
                    "-silent",
                ],
                subfinder_file,
            )
        )

        if rc == 127:

            print(
                "[-] subfinder not installed."
            )

        elif rc == 130:

            print(
                "[!] subfinder interrupted."
            )

        else:

            for line in (
                subfinder_output.splitlines()
            ):

                hostname = (
                    line.strip().lower()
                )

                if not hostname:
                    continue

                if hostname.endswith(
                    f".{target_domain.lower()}"
                ):
                    found_subdomains.add(
                        hostname
                    )

        # -----------------------------------------------------
        # Save results
        # -----------------------------------------------------

        subdomains_file.write_text(
            "\n".join(
                sorted(found_subdomains)
            )
            + (
                "\n"
                if found_subdomains
                else ""
            ),
            encoding="utf-8",
        )

        print()
        print(
            "[+] Final discovered hosts:"
        )

        for hostname in sorted(
            found_subdomains
        ):
            print(
                f"    - {hostname}"
            )

        # -----------------------------------------------------
        # Update /etc/hosts ONCE
        # -----------------------------------------------------

        update_hosts_file(
            ip,
            found_subdomains,
        )

    # =========================================================
    # 9. Endpoint fuzzing
    # =========================================================

    print_section(
        "9/9 - Web endpoint fuzzing"
    )

    if not WEB_WORDLIST.exists():

        print(
            "[!] Missing wordlist:"
        )

        print(
            f"    {WEB_WORDLIST}"
        )

    else:

        print(
            f"[+] Target: "
            f"{base_url}/FUZZ"
        )

        print(
            f"[+] Wordlist: "
            f"{WEB_WORDLIST}"
        )

        print(
            "[+] Starting ffuf endpoint fuzzing..."
        )

        rc, _ = run_command(
            [
                "ffuf",
                "-w",
                str(WEB_WORDLIST),
                "-u",
                f"{base_url}/FUZZ",
                "-mc",
                "200,204,301,302,307,401,403",
                "-ac",
            ],
            directories_file,
        )

        if rc == 130:
            print(
                "[!] Endpoint fuzzing interrupted."
            )

        else:
            print(
                "[+] Endpoint fuzzing finished."
            )

    # =========================================================
    # Summary
    # =========================================================

    print_section(
        "RECON COMPLETE"
    )

    print(
        f"[+] Target : {ip}"
    )

    print(
        "[+] Ports  : "
        + ", ".join(open_ports)
    )

    print(
        "[+] HTTP   : "
        + ", ".join(http_ports)
    )

    if found_subdomains:

        print(
            "[+] Hosts:"
        )

        for hostname in sorted(
            found_subdomains
        ):
            print(
                f"    - {hostname}"
            )

    print()
    print(
        f"[+] Results: "
        f"{output_dir}"
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(
            main()
        )
    except KeyboardInterrupt:
        print()
        print(
            "[!] Recon interrupted by user."
        )
        sys.exit(130)
