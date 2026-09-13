#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse


SECLISTS = Path("/usr/share/seclists")

SUBDOMAIN_WORDLIST = (
    SECLISTS / "Discovery/DNS/subdomains-top1million-5000.txt"
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


def run_command(command, output_file=None):
    print(f"[+] Running: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(f"[!] Command not found: {command[0]}")
        return 127, ""

    if output_file:
        Path(output_file).write_text(
            result.stdout,
            encoding="utf-8",
        )

    return result.returncode, result.stdout


def parse_open_ports(nmap_output):
    ports = []

    for line in nmap_output.splitlines():
        match = re.match(
            r"^\s*(\d+)/tcp\s+open\s+",
            line,
        )

        if match:
            ports.append(match.group(1))

    return sorted(set(ports), key=int)


def detect_http_ports(open_ports):
    return [
        port
        for port in open_ports
        if port in HTTP_PORTS
    ]


def http_request(url, timeout=8):
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "HTB-Recon/1.0",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            return (
                response.geturl(),
                response.status,
                response.headers,
                response.read(),
            )

    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location")

        if location:
            final_url = urljoin(url, location)
        else:
            final_url = url

        return (
            final_url,
            exc.code,
            exc.headers,
            exc.read(),
        )

    except urllib.error.URLError:
        return None, None, None, None

    except Exception:
        return None, None, None, None


def extract_hostname(url):
    try:
        hostname = urlparse(url).hostname

        if hostname:
            return hostname
    except Exception:
        pass

    match = re.search(
        r"https?://([^/:]+)",
        url,
    )

    if match:
        return match.group(1)

    return None


def update_hosts_file(ip, hostname):
    if not hostname:
        return False

    try:
        content = HOSTS_FILE.read_text(
            encoding="utf-8",
        )
    except PermissionError:
        print(
            "[!] Cannot read /etc/hosts. "
            "Run the script with sudo."
        )
        return False

    lines = content.splitlines()

    try:
        start = lines.index(HTB_START)
        end = lines.index(
            HTB_END,
            start + 1,
        )
    except ValueError:
        print(
            "[!] Could not find "
            "###HTB / ###END_HTB markers."
        )
        return False

    # Comment all active lines inside the HTB section.
    for i in range(start + 1, end):
        stripped = lines[i].strip()

        if stripped and not stripped.startswith("#"):
            lines[i] = "#" + lines[i]

    # Remove old occurrences of this hostname
    # inside the managed HTB section.
    filtered = []

    for i, line in enumerate(lines):
        if start < i < end:
            uncommented = line.lstrip("#").strip()

            if re.search(
                rf"(^|\s){re.escape(hostname)}(\s|$)",
                uncommented,
            ):
                continue

        filtered.append(line)

    lines = filtered

    start = lines.index(HTB_START)
    end = lines.index(
        HTB_END,
        start + 1,
    )

    entry = f"{ip:<24}{hostname}"

    # Add target as the last active HTB entry.
    lines.insert(end, entry)

    try:
        HOSTS_FILE.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
    except PermissionError:
        print(
            "[!] Cannot write /etc/hosts. "
            "Run the script with sudo."
        )
        return False

    print(
        f"[+] /etc/hosts updated: {entry}"
    )

    return True


def extract_domains(text):
    return sorted(
        set(
            domain.lower()
            for domain in re.findall(
                r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b",
                text,
            )
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "HTB recon automation: "
            "Nmap + redirect detection + "
            "subdomains + ffuf"
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
        output_dir / "nmap-full.txt"
    )

    nmap_services = (
        output_dir / "nmap-services.txt"
    )

    redirects_file = (
        output_dir / "redirects.txt"
    )

    subdomains_file = (
        output_dir / "subdomains.txt"
    )

    subfinder_file = (
        output_dir / "subfinder.txt"
    )

    vhosts_file = (
        output_dir / "ffuf-vhosts.txt"
    )

    directories_file = (
        output_dir / "ffuf-directories.txt"
    )

    print(
        f"[+] Target: {ip}"
    )

    print(
        f"[+] Output: {output_dir}"
    )

    # =========================================================
    # 1. Full TCP scan
    # =========================================================

    _, full_output = run_command(
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

    open_ports = parse_open_ports(
        full_output
    )

    if not open_ports:
        print(
            "[!] No open TCP ports found."
        )
        return 1

    print(
        "[+] Open ports: "
        + ", ".join(open_ports)
    )

    # =========================================================
    # 2. Version + default scripts
    # =========================================================

    run_command(
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

    # =========================================================
    # 3. Detect HTTP services
    # =========================================================

    http_ports = detect_http_ports(
        open_ports
    )

    if not http_ports:
        print(
            "[+] No common HTTP/HTTPS ports found."
        )
        return 0

    print(
        "[+] HTTP ports detected: "
        + ", ".join(http_ports)
    )

    discovered_hosts = set()

    # =========================================================
    # 4. Redirect detection
    # =========================================================

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

            url = f"{scheme}://{ip}/"

            final_url, status, headers, _ = (
                http_request(url)
            )

            location = (
                headers.get("Location")
                if headers
                else None
            )

            if location:

                redirect_url = urljoin(
                    url,
                    location,
                )

                print(
                    f"[+] Redirect: "
                    f"{url} -> {redirect_url}"
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

                if (
                    hostname
                    and hostname != ip
                ):
                    discovered_hosts.add(
                        hostname
                    )

            elif final_url and final_url != url:

                print(
                    f"[+] Redirect: "
                    f"{url} -> {final_url}"
                )

                rf.write(
                    f"{url} -> "
                    f"{final_url}\n"
                )

                hostname = (
                    extract_hostname(
                        final_url
                    )
                )

                if (
                    hostname
                    and hostname != ip
                ):
                    discovered_hosts.add(
                        hostname
                    )

            else:

                print(
                    f"[-] No redirect: "
                    f"{url} "
                    f"(HTTP {status})"
                )

                rf.write(
                    f"{url} -> "
                    f"no redirect "
                    f"(HTTP {status})\n"
                )

    # =========================================================
    # 5. Update /etc/hosts
    # =========================================================

    for hostname in sorted(
        discovered_hosts
    ):
        update_hosts_file(
            ip,
            hostname,
        )

    # =========================================================
    # 6. Select target hostname
    # =========================================================

    if discovered_hosts:
        target_domain = sorted(
            discovered_hosts
        )[0]

        print(
            f"[+] Web target: "
            f"{target_domain}"
        )

    else:
        target_domain = None

        print(
            "[+] No hostname discovered, "
            "using IP."
        )

    # =========================================================
    # 7. Select HTTP scheme
    # =========================================================

    if (
        "443" in http_ports
        and "80" not in http_ports
    ):
        scheme = "https"
    else:
        scheme = "http"

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

    # =========================================================
    # 8. Subdomain / VHost enumeration
    # =========================================================

    if target_domain:

        if not SUBDOMAIN_WORDLIST.exists():

            print(
                "[!] Missing wordlist: "
                f"{SUBDOMAIN_WORDLIST}"
            )

        else:

            run_command(
                [
                    "ffuf",
                    "-w",
                    str(SUBDOMAIN_WORDLIST),
                    "-u",
                    f"{scheme}://{target_domain}/",
                    "-H",
                    f"Host: FUZZ.{target_domain}",
                    "-mc",
                    "200,204,301,302,307,401,403",
                    "-ac",
                ],
                vhosts_file,
            )

        # -----------------------------------------------------
        # subfinder
        # -----------------------------------------------------

        rc, subfinder_output = run_command(
            [
                "subfinder",
                "-d",
                target_domain,
                "-silent",
            ],
            subfinder_file,
        )

        found_subdomains = set()

        if rc != 127:

            for line in (
                subfinder_output.splitlines()
            ):
                line = line.strip()

                if line:
                    found_subdomains.add(
                        line
                    )

        try:

            vhost_text = (
                vhosts_file.read_text(
                    encoding="utf-8"
                )
            )

            found_subdomains.update(
                extract_domains(
                    vhost_text
                )
            )

        except FileNotFoundError:
            pass

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

        # Add discovered subdomains to /etc/hosts.
        for hostname in sorted(
            found_subdomains
        ):
            update_hosts_file(
                ip,
                hostname,
            )

    else:

        subdomains_file.write_text(
            "",
            encoding="utf-8",
        )

    # =========================================================
    # 9. Endpoint fuzzing
    # =========================================================

    if not WEB_WORDLIST.exists():

        print(
            "[!] Missing wordlist: "
            f"{WEB_WORDLIST}"
        )

    else:

        run_command(
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

    print()
    print(
        "[+] Recon complete."
    )

    print(
        f"[+] Results: {output_dir}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
