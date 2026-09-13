#!/usr/bin/env python3

import argparse
import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
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

FFUF_MATCH_CODES = "200,204,301,302,307,401,403"
FFUF_THREADS = "30"


class NoRedirectHandler(
    urllib.request.HTTPRedirectHandler
):
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


SSL_CONTEXT = ssl._create_unverified_context()

HTTP_OPENER = urllib.request.build_opener(
    NoRedirectHandler()
)

HTTPS_OPENER = urllib.request.build_opener(
    NoRedirectHandler()
)


def print_section(title):
    print()
    print("=" * 72)
    print(f"[+] {title}")
    print("=" * 72)


def run_command(command, output_file=None):
    print()
    print(f"[>] {' '.join(command)}")

    if output_file:
        print(f"[>] Output: {output_file}")

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
            "[!] Command interrupted."
        )
        return 130, ""

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
            ports.append(
                match.group(1)
            )

    return sorted(
        set(ports),
        key=int,
    )


def parse_nmap_xml(xml_file):
    services = {}

    try:
        root = ET.parse(
            xml_file
        ).getroot()

    except (
        FileNotFoundError,
        ET.ParseError,
    ):
        return services

    for port in root.findall(
        ".//port"
    ):
        protocol = port.get(
            "protocol"
        )

        portid = port.get(
            "portid"
        )

        if protocol != "tcp" or not portid:
            continue

        state = port.find(
            "state"
        )

        if (
            state is None
            or state.get("state") != "open"
        ):
            continue

        service = port.find(
            "service"
        )

        if service is None:
            continue

        services[portid] = {
            "name": service.get(
                "name",
                ""
            ),
            "product": service.get(
                "product",
                ""
            ),
            "version": service.get(
                "version",
                ""
            ),
            "tunnel": service.get(
                "tunnel",
                ""
            ),
        }

    return services


def is_web_service(service):
    name = service.get(
        "name",
        ""
    ).lower()

    product = service.get(
        "product",
        ""
    ).lower()

    tunnel = service.get(
        "tunnel",
        ""
    ).lower()

    web_names = {
        "http",
        "https",
        "http-alt",
        "http-proxy",
        "http-api",
        "http-rpc-epmap",
    }

    if name in web_names:
        return True

    if (
        name.startswith("http")
        or "http" in name
    ):
        return True

    if tunnel == "ssl" and (
        "http" in name
        or "apache" in product
        or "nginx" in product
    ):
        return True

    return False


def get_web_scheme(service):
    name = service.get(
        "name",
        ""
    ).lower()

    tunnel = service.get(
        "tunnel",
        ""
    ).lower()

    if (
        name == "https"
        or tunnel == "ssl"
    ):
        return "https"

    return "http"


def http_request(
    url,
    timeout=8,
):
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "HTB-Recon/1.0",
        },
    )

    opener = (
        HTTPS_OPENER
        if url.startswith("https://")
        else HTTP_OPENER
    )

    try:
        if url.startswith(
            "https://"
        ):
            response = opener.open(
                request,
                timeout=timeout,
                context=SSL_CONTEXT,
            )
        else:
            response = opener.open(
                request,
                timeout=timeout,
            )

        return (
            response.status,
            response.headers,
        )

    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            exc.headers,
        )

    except urllib.error.URLError as exc:
        print(
            f"[!] HTTP error: {exc}"
        )
        return (
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
        )


def extract_hostname(
    url
):
    if not url:
        return None

    try:
        hostname = urlparse(
            url
        ).hostname

        if hostname:
            return hostname.lower()

    except Exception:
        pass

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
    hostnames = sorted(
        {
            hostname.strip().lower()
            for hostname in hostnames
            if hostname.strip()
        }
    )

    if not hostnames:
        return False

    try:
        content = HOSTS_FILE.read_text(
            encoding="utf-8"
        )

    except PermissionError:
        print(
            "[!] Cannot read /etc/hosts."
        )

        print(
            "[!] Run with sudo."
        )

        return False

    lines = content.splitlines()

    start, end = get_htb_section(
        lines
    )

    if start is None:
        print(
            "[!] Missing "
            "###HTB / ###END_HTB."
        )

        return False

    # ---------------------------------------------------------
    # Comment all active HTB entries
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Insert one active entry
    # ---------------------------------------------------------

    start, end = get_htb_section(
        lines
    )

    entry = (
        f"{ip}\t"
        f"{' '.join(hostnames)}"
    )

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
            "[!] Run with sudo."
        )

        return False

    print(
        f"[+] /etc/hosts:"
    )

    print(
        f"    {entry}"
    )

    return True


def parse_ffuf_json(
    json_file,
):
    try:
        data = json.loads(
            Path(json_file).read_text(
                encoding="utf-8"
            )
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ):
        return []

    return data.get(
        "results",
        []
    )


def parse_vhosts(
    json_file,
    base_domain,
):
    hosts = set()

    results = parse_ffuf_json(
        json_file
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
            hosts.add(
                host
            )

    return hosts


def print_vhost_results(
    json_file,
):
    results = parse_ffuf_json(
        json_file
    )

    if not results:
        print(
            "[-] No VHosts found."
        )
        return

    print(
        "[+] VHosts:"
    )

    for result in results:

        host = result.get(
            "host",
            "?"
        )

        status = result.get(
            "status",
            "?"
        )

        size = result.get(
            "length",
            "?"
        )

        words = result.get(
            "words",
            "?"
        )

        print(
            f"    {host:<35}"
            f"[{status}] "
            f"Size:{size} "
            f"Words:{words}"
        )


def print_directory_results(
    json_file,
):
    results = parse_ffuf_json(
        json_file
    )

    if not results:
        print(
            "[-] No endpoints found."
        )
        return

    print(
        "[+] Endpoints:"
    )

    for result in results:

        url = result.get(
            "url",
            "?"
        )

        status = result.get(
            "status",
            "?"
        )

        size = result.get(
            "length",
            "?"
        )

        words = result.get(
            "words",
            "?"
        )

        print(
            f"    [{status}] "
            f"{url} "
            f"(size:{size}, "
            f"words:{words})"
        )


def run_vhost_fuzzing(
    base_url,
    domain,
    output_dir,
):
    if not SUBDOMAIN_WORDLIST.exists():

        print(
            "[!] VHost wordlist missing:"
        )

        print(
            f"    {SUBDOMAIN_WORDLIST}"
        )

        return set()

    json_file = (
        output_dir / "vhosts.json"
    )

    text_file = (
        output_dir / "vhosts.txt"
    )

    print(
        "[+] Starting VHost fuzzing..."
    )

    rc, _ = run_command(
        [
            "ffuf",
            "-s",
            "-t",
            FFUF_THREADS,
            "-w",
            str(
                SUBDOMAIN_WORDLIST
            ),
            "-u",
            f"{base_url}/",
            "-H",
            f"Host: FUZZ.{domain}",
            "-mc",
            FFUF_MATCH_CODES,
            "-ac",
            "-of",
            "json",
            "-o",
            str(json_file),
        ],
        text_file,
    )

    if rc == 130:
        print(
            "[!] VHost fuzzing interrupted."
        )

        return set()

    print_vhost_results(
        json_file
    )

    return parse_vhosts(
        json_file,
        domain,
    )


def run_directory_fuzzing(
    base_url,
    output_dir,
):
    if not WEB_WORDLIST.exists():

        print(
            "[!] Web wordlist missing:"
        )

        print(
            f"    {WEB_WORDLIST}"
        )

        return

    json_file = (
        output_dir
        / "directories.json"
    )

    text_file = (
        output_dir
        / "directories.txt"
    )

    print(
        "[+] Starting endpoint fuzzing..."
    )

    rc, _ = run_command(
        [
            "ffuf",
            "-s",
            "-t",
            FFUF_THREADS,
            "-w",
            str(WEB_WORDLIST),
            "-u",
            f"{base_url}/FUZZ",
            "-mc",
            FFUF_MATCH_CODES,
            "-ac",
            "-of",
            "json",
            "-o",
            str(json_file),
        ],
        text_file,
    )

    if rc == 130:

        print(
            "[!] Endpoint fuzzing interrupted."
        )

        return

    print_directory_results(
        json_file
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "HTB reconnaissance wrapper"
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
        help="Output directory",
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

    nmap_xml = (
        output_dir
        / "nmap-services.xml"
    )

    redirects_file = (
        output_dir
        / "redirects.txt"
    )

    print()
    print("=" * 72)
    print(" HTB RECON")
    print("=" * 72)

    print(
        f"[+] Target: {ip}"
    )

    print(
        f"[+] Output: {output_dir}"
    )

    print("=" * 72)

    # =========================================================
    # 1. Full TCP scan
    # =========================================================

    print_section(
        "1/4 - Full TCP scan"
    )

    rc, full_output = run_command(
        [
            "nmap",
            "-n",
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
        return 130

    open_ports = parse_open_ports(
        full_output
    )

    if not open_ports:

        print(
            "[!] No open TCP ports."
        )

        return 1

    print(
        "[+] Open ports:"
    )

    for port in open_ports:
        print(
            f"    - {port}"
        )

    # =========================================================
    # 2. Service / version detection
    # =========================================================

    print_section(
        "2/4 - Service and version detection"
    )

    rc, _ = run_command(
        [
            "nmap",
            "-n",
            "-sC",
            "-sV",
            "-p",
            ",".join(open_ports),
            "-oX",
            str(nmap_xml),
            ip,
        ],
        nmap_services,
    )

    if rc == 130:
        return 130

    services = parse_nmap_xml(
        nmap_xml
    )

    if services:

        print(
            "[+] Detected services:"
        )

        for port in sorted(
            services,
            key=int,
        ):

            service = services[
                port
            ]

            name = service.get(
                "name",
                "-"
            )

            product = service.get(
                "product",
                ""
            )

            version = service.get(
                "version",
                ""
            )

            description = (
                f"{product} {version}"
            ).strip()

            if description:
                print(
                    f"    {port}/tcp "
                    f"{name:<12} "
                    f"{description}"
                )

            else:
                print(
                    f"    {port}/tcp "
                    f"{name}"
                )

    # =========================================================
    # 3. Detect ALL web services
    # =========================================================

    print_section(
        "3/4 - Web service enumeration"
    )

    web_services = {}

    for port, service in services.items():

        if is_web_service(
            service
        ):
            web_services[
                port
            ] = service

    if not web_services:

        print(
            "[-] No HTTP/HTTPS services detected."
        )

        print(
            "[+] Recon complete."
        )

        return 0

    print(
        "[+] Web services:"
    )

    for port in sorted(
        web_services,
        key=int,
    ):

        service = web_services[
            port
        ]

        scheme = get_web_scheme(
            service
        )

        print(
            f"    - {scheme}://"
            f"{ip}:{port}"
        )

    # =========================================================
    # 4. Enumerate every web service
    # =========================================================

    print_section(
        "4/4 - HTTP enumeration"
    )

    all_hosts = set()

    for port in sorted(
        web_services,
        key=int,
    ):

        service = web_services[
            port
        ]

        scheme = get_web_scheme(
            service
        )

        base_url = (
            f"{scheme}://"
            f"{ip}:{port}"
        )

        # -----------------------------------------------------
        # Per-port output directory
        # -----------------------------------------------------

        port_dir = (
            output_dir
            / f"web-{port}"
        )

        port_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print_section(
            f"Web target {scheme}://{ip}:{port}"
        )

        print(
            f"[+] Results: {port_dir}"
        )

        # -----------------------------------------------------
        # Redirect detection
        # -----------------------------------------------------

        print(
            "[+] Checking redirect..."
        )

        status, headers = (
            http_request(
                f"{base_url}/"
            )
        )

        redirect_file = (
            port_dir
            / "redirect.txt"
        )

        redirect_file.write_text(
            "",
            encoding="utf-8",
        )

        hostname = None

        if headers:

            location = headers.get(
                "Location"
            )

            if location:

                redirect_url = urljoin(
                    f"{base_url}/",
                    location,
                )

                hostname = (
                    extract_hostname(
                        redirect_url
                    )
                )

                print(
                    f"[+] Redirect: "
                    f"{status} -> "
                    f"{redirect_url}"
                )

                redirect_file.write_text(
                    redirect_url
                    + "\n",
                    encoding="utf-8",
                )

                if hostname:

                    print(
                        f"[+] Hostname: "
                        f"{hostname}"
                    )

                    all_hosts.add(
                        hostname
                    )

            else:

                print(
                    f"[-] No redirect "
                    f"(HTTP {status})"
                )

                redirect_file.write_text(
                    f"HTTP {status}\n",
                    encoding="utf-8",
                )

        else:

            print(
                "[-] No HTTP response."
            )

        # -----------------------------------------------------
        # /etc/hosts
        # -----------------------------------------------------

        if hostname:

            update_hosts_file(
                ip,
                all_hosts,
            )

        # -----------------------------------------------------
        # VHost fuzzing
        # -----------------------------------------------------

        if hostname:

            vhosts = run_vhost_fuzzing(
                base_url,
                hostname,
                port_dir,
            )

            all_hosts.update(
                vhosts
            )

            if vhosts:

                update_hosts_file(
                    ip,
                    all_hosts,
                )

        else:

            print(
                "[-] Skipping VHost "
                "fuzzing: no domain."
            )

        # -----------------------------------------------------
        # Endpoint fuzzing
        # -----------------------------------------------------

        run_directory_fuzzing(
            base_url,
            port_dir,
        )

    # =========================================================
    # Final /etc/hosts update
    # =========================================================

    if all_hosts:

        print_section(
            "Updating /etc/hosts"
        )

        update_hosts_file(
            ip,
            all_hosts,
        )

    # =========================================================
    # Summary
    # =========================================================

    print_section(
        "RECON COMPLETE"
    )

    print(
        f"[+] Target: {ip}"
    )

    print(
        "[+] Open ports: "
        + ", ".join(
            open_ports
        )
    )

    print(
        "[+] Web ports: "
        + ", ".join(
            sorted(
                web_services,
                key=int,
            )
        )
    )

    if all_hosts:

        print(
            "[+] Hostnames:"
        )

        for host in sorted(
            all_hosts
        ):
            print(
                f"    - {host}"
            )

    print()
    print(
        f"[+] Results: {output_dir}"
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
            "[!] Recon interrupted."
        )
        sys.exit(130)
