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

SSL_CONTEXT = ssl._create_unverified_context()


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


HTTP_OPENER = urllib.request.build_opener(
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
        print("[!] Interrupted by user.")
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

        if (
            protocol != "tcp"
            or not portid
        ):
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

        scripts = []

        for script in port.findall(
            "./script"
        ):
            script_id = script.get(
                "id"
            )

            output = script.get(
                "output"
            )

            if script_id:
                scripts.append(
                    {
                        "id": script_id,
                        "output": output or "",
                    }
                )

        services[portid] = {
            "name": service.get(
                "name",
                "",
            ),
            "product": service.get(
                "product",
                "",
            ),
            "version": service.get(
                "version",
                "",
            ),
            "extrainfo": service.get(
                "extrainfo",
                "",
            ),
            "tunnel": service.get(
                "tunnel",
                "",
            ),
            "scripts": scripts,
        }

    return services


def is_web_service(service):
    name = service.get(
        "name",
        "",
    ).lower()

    product = service.get(
        "product",
        "",
    ).lower()

    tunnel = service.get(
        "tunnel",
        "",
    ).lower()

    web_names = {
        "http",
        "https",
        "http-alt",
        "http-proxy",
    }

    if name in web_names:
        return True

    if (
        name.startswith("http")
        or "http" in name
    ):
        return True

    if (
        tunnel == "ssl"
        and (
            "http" in name
            or "apache" in product
            or "nginx" in product
        )
    ):
        return True

    return False


def get_web_scheme(service):
    name = service.get(
        "name",
        "",
    ).lower()

    tunnel = service.get(
        "tunnel",
        "",
    ).lower()

    if (
        name == "https"
        or tunnel == "ssl"
    ):
        return "https"

    return "http"


def http_request(url, timeout=8):
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "HTB-Recon/1.0",
        },
    )

    try:
        if url.startswith(
            "https://"
        ):
            response = HTTP_OPENER.open(
                request,
                timeout=timeout,
                context=SSL_CONTEXT,
            )
        else:
            response = HTTP_OPENER.open(
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

    except (
        urllib.error.URLError,
        TimeoutError,
    ) as exc:
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


def extract_hostname(url):
    if not url:
        return None

    try:
        parsed = urlparse(
            url
        )

        if parsed.hostname:
            return parsed.hostname.lower()

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
            "###HTB / ###END_HTB markers."
        )

        return False

    # Comment every active HTB entry.
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

    suffix = (
        f".{base_domain.lower()}"
    )

    for result in parse_ffuf_json(
        json_file
    ):
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
        "[+] VHosts found:"
    )

    for result in results:

        host = result.get(
            "host",
            "?",
        )

        status = result.get(
            "status",
            "?",
        )

        size = result.get(
            "length",
            "?",
        )

        words = result.get(
            "words",
            "?",
        )

        print(
            f"    {host:<35}"
            f"[{status}] "
            f"Size:{size} "
            f"Words:{words}"
        )


def print_endpoint_results(
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
        "[+] Endpoints found:"
    )

    for result in results:

        url = result.get(
            "url",
            "?",
        )

        status = result.get(
            "status",
            "?",
        )

        size = result.get(
            "length",
            "?",
        )

        words = result.get(
            "words",
            "?",
        )

        print(
            f"    [{status}] "
            f"{url} "
            f"(size:{size}, "
            f"words:{words})"
        )


def endpoint_results_for_summary(
    json_file,
):
    results = []

    for result in parse_ffuf_json(
        json_file
    ):
        url = result.get(
            "url"
        )

        if not url:
            continue

        parsed = urlparse(
            url
        )

        results.append(
            {
                "path": (
                    parsed.path
                    or "/"
                ),
                "status": result.get(
                    "status"
                ),
                "size": result.get(
                    "length"
                ),
                "words": result.get(
                    "words"
                ),
                "lines": result.get(
                    "lines"
                ),
            }
        )

    return results


def run_vhost_fuzzing(
    base_url,
    domain,
    output_dir,
):
    if not SUBDOMAIN_WORDLIST.exists():

        print(
            "[!] Missing VHost wordlist:"
        )

        print(
            f"    {SUBDOMAIN_WORDLIST}"
        )

        return set()

    json_file = (
        output_dir
        / "vhosts.json"
    )

    text_file = (
        output_dir
        / "vhosts.txt"
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
            str(
                json_file
            ),
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


def run_endpoint_fuzzing(
    base_url,
    hostname,
    output_dir,
):
    if not WEB_WORDLIST.exists():

        print(
            "[!] Missing endpoint wordlist:"
        )

        print(
            f"    {WEB_WORDLIST}"
        )

        return

    safe_hostname = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        hostname,
    )

    json_file = (
        output_dir
        / f"endpoints-{safe_hostname}.json"
    )

    text_file = (
        output_dir
        / f"endpoints-{safe_hostname}.txt"
    )

    print(
        f"[+] Endpoint fuzzing: "
        f"{hostname}"
    )

    rc, _ = run_command(
        [
            "ffuf",
            "-s",
            "-t",
            FFUF_THREADS,
            "-w",
            str(
                WEB_WORDLIST
            ),
            "-u",
            f"{base_url}/FUZZ",
            "-H",
            f"Host: {hostname}",
            "-mc",
            FFUF_MATCH_CODES,
            "-ac",
            "-of",
            "json",
            "-o",
            str(
                json_file
            ),
        ],
        text_file,
    )

    if rc == 130:
        print(
            "[!] Endpoint fuzzing interrupted."
        )

        return

    print_endpoint_results(
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

    summary_file = (
        output_dir
        / "summary.json"
    )

    summary = {
        "target": ip,
        "ports": [],
        "hosts": [],
        "web": [],
    }

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
            "[!] No open TCP ports found."
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
    # 2. Service detection
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

    for port in sorted(
        services,
        key=int,
    ):
        service = services[
            port
        ]

        summary["ports"].append(
            {
                "port": int(port),
                "protocol": "tcp",
                "service": service.get(
                    "name"
                ) or "unknown",
                "product": service.get(
                    "product"
                ) or "",
                "version": service.get(
                    "version"
                ) or "",
                "extrainfo": service.get(
                    "extrainfo"
                ) or "",
            }
        )

        name = service.get(
            "name",
            "",
        )

        product = service.get(
            "product",
            "",
        )

        version = service.get(
            "version",
            "",
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
                f"{name or 'unknown'}"
            )

    # =========================================================
    # 3. Detect all web services
    # =========================================================

    print_section(
        "3/4 - Web service discovery"
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
            "[-] No web services detected."
        )

        summary_file.write_text(
            json.dumps(
                summary,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"[+] Summary: "
            f"{summary_file}"
        )

        return 0

    print(
        "[+] Web services:"
    )

    for port in sorted(
        web_services,
        key=int,
    ):

        scheme = get_web_scheme(
            web_services[
                port
            ]
        )

        print(
            f"    - "
            f"{scheme}://"
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

        ip_base_url = (
            f"{scheme}://"
            f"{ip}:{port}"
        )

        port_dir = (
            output_dir
            / f"web-{port}"
        )

        port_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        web_summary = {
            "port": int(port),
            "scheme": scheme,
            "base": ip_base_url,
            "redirect": None,
            "hosts": [],
            "vhosts": [],
            "endpoints": {},
        }

        print_section(
            f"Web target: "
            f"{ip_base_url}"
        )

        # -----------------------------------------------------
        # Redirect
        # -----------------------------------------------------

        print(
            "[+] Checking redirect..."
        )

        status, headers = http_request(
            f"{ip_base_url}/"
        )

        redirect_value = None

        if headers:

            location = headers.get(
                "Location"
            )

            if location:

                redirect_value = urljoin(
                    f"{ip_base_url}/",
                    location,
                )

                hostname = extract_hostname(
                    redirect_value
                )

                print(
                    f"[+] Redirect: "
                    f"{status} -> "
                    f"{redirect_value}"
                )

                (
                    port_dir
                    / "redirect.txt"
                ).write_text(
                    redirect_value
                    + "\n",
                    encoding="utf-8",
                )

                web_summary[
                    "redirect"
                ] = redirect_value

                if hostname:

                    print(
                        f"[+] Hostname: "
                        f"{hostname}"
                    )

                    all_hosts.add(
                        hostname
                    )

                    web_summary[
                        "hosts"
                    ].append(
                        hostname
                    )

            else:

                print(
                    f"[-] No redirect "
                    f"(HTTP {status})"
                )

                (
                    port_dir
                    / "redirect.txt"
                ).write_text(
                    f"HTTP {status}\n",
                    encoding="utf-8",
                )

        else:

            print(
                "[-] No HTTP response."
            )

            (
                port_dir
                / "redirect.txt"
            ).write_text(
                "No HTTP response\n",
                encoding="utf-8",
            )

        # -----------------------------------------------------
        # Initial /etc/hosts update
        # -----------------------------------------------------

        if all_hosts:

            update_hosts_file(
                ip,
                all_hosts,
            )

        # -----------------------------------------------------
        # Select primary hostname
        # -----------------------------------------------------

        primary_hostname = None

        if web_summary["hosts"]:

            primary_hostname = (
                web_summary[
                    "hosts"
                ][0]
            )

        if primary_hostname:

            # -------------------------------------------------
            # VHost fuzzing
            # -------------------------------------------------

            vhosts = run_vhost_fuzzing(
                ip_base_url,
                primary_hostname,
                port_dir,
            )

            web_summary[
                "vhosts"
            ] = sorted(
                vhosts
            )

            all_hosts.update(
                vhosts
            )

        else:

            print(
                "[-] No hostname available "
                "for VHost fuzzing."
            )

        # -----------------------------------------------------
        # Build complete host set for this web service.
        #
        # The primary hostname must always be fuzzed for
        # endpoints, plus every discovered VHost.
        # -----------------------------------------------------

        web_hosts = set()

        if primary_hostname:
            web_hosts.add(
                primary_hostname
            )

        web_hosts.update(
            web_summary[
                "vhosts"
            ]
        )

        # -----------------------------------------------------
        # Update hosts before endpoint fuzzing
        # -----------------------------------------------------

        if web_hosts:

            all_hosts.update(
                web_hosts
            )

            update_hosts_file(
                ip,
                all_hosts,
            )

        # -----------------------------------------------------
        # Endpoint fuzzing for EVERY hostname
        # -----------------------------------------------------

        if web_hosts:

            for hostname in sorted(
                web_hosts
            ):

                endpoint_base = (
                    f"{scheme}://"
                    f"{ip}:{port}"
                )

                run_endpoint_fuzzing(
                    endpoint_base,
                    hostname,
                    port_dir,
                )

                safe_hostname = re.sub(
                    r"[^a-zA-Z0-9._-]",
                    "_",
                    hostname,
                )

                endpoint_json = (
                    port_dir
                    / f"endpoints-"
                    f"{safe_hostname}.json"
                )

                web_summary[
                    "endpoints"
                ][hostname] = (
                    endpoint_results_for_summary(
                        endpoint_json
                    )
                )

        else:

            # No domain was found, so fuzz the IP directly.
            run_endpoint_fuzzing(
                ip_base_url,
                ip,
                port_dir,
            )

            web_summary[
                "endpoints"
            ][ip] = (
                endpoint_results_for_summary(
                    port_dir
                    / "endpoints-"
                    f"{ip}.json"
                )
            )

        summary[
            "web"
        ].append(
            web_summary
        )

    # =========================================================
    # Final /etc/hosts update
    # =========================================================

    if all_hosts:

        print_section(
            "Final /etc/hosts update"
        )

        update_hosts_file(
            ip,
            all_hosts,
        )

    summary["hosts"] = sorted(
        all_hosts
    )

    # =========================================================
    # Save summary
    # =========================================================

    summary_file.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    # =========================================================
    # Final summary
    # =========================================================

    print_section(
        "RECON COMPLETE"
    )

    print(
        f"[+] Target: {ip}"
    )

    print(
        "[+] Open ports:"
    )

    for port in summary[
        "ports"
    ]:

        description = (
            f"{port['product']} "
            f"{port['version']}"
        ).strip()

        if description:

            print(
                f"    {port['port']}/tcp "
                f"{port['service']} "
                f"- {description}"
            )

        else:

            print(
                f"    {port['port']}/tcp "
                f"{port['service']}"
            )

    if summary["hosts"]:

        print()
        print(
            "[+] Hosts:"
        )

        for hostname in summary[
            "hosts"
        ]:

            print(
                f"    - {hostname}"
            )

    print()
    print(
        f"[+] Summary: "
        f"{summary_file}"
    )

    print(
        f"[+] Details: "
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
            "[!] Recon interrupted."
        )

        sys.exit(130)
