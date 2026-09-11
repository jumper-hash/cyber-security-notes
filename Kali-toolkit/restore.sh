#!/usr/bin/env bash
# ============================================================
# Kali Restore v 2.3
# Author jumper-hash
# Run: chmod +x kali-restore.sh && sudo ./kali-restore.sh
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="${SCRIPT_DIR}/tools"
STAGE_DIR="${TOOLS_DIR}/staging"
DATE_TAG="$(date +%Y%m%d)"
LOGFILE="${TOOLS_DIR}/kali-restore-${DATE_TAG}.log"

mkdir -p "$TOOLS_DIR" "$STAGE_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()   { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[x]${NC} $1"; }
info()  { echo -e "${CYAN}[*]${NC} $1"; }

# ------------------------------------------------------------
check_root() {
    if [[ $EUID -ne 0 ]]; then
        err "This script requires root privileges (sudo)."
        exit 1
    fi
}

# ------------------------------------------------------------
# Install APT packages one-by-one so missing pkgs don't kill the script
# ------------------------------------------------------------
install_apt_pkgs() {
    log "Updating package lists..."
    apt update -qq

    log "Installing APT packages..."

    local -a apt_pkgs=(
        seclists enum4linux smbclient smbmap impacket-scripts
        netexec bloodhound chisel ligolo-ng ffuf gobuster dirb
        nikto wpscan evil-winrm hydra john hashcat
        metasploit-framework sqlmap burpsuite wireshark responder
        mitm6 bettercap exploitdb jq netcat-openbsd ncat tmux
        rlwrap xclip python3-venv python3-pip bat fzf pipx
        power-profiles-daemon
    )

    local success=0 fail=0
    for pkg in "${apt_pkgs[@]}"; do
        if apt install -y "$pkg" &>> "${LOGFILE}"; then
            ((++success))
        else
            warn "Package '$pkg' not found in repos — skipping."
            ((++fail))
        fi
    done

    log "APT packages: $success installed, $fail skipped."
}

# ------------------------------------------------------------
# pip packages for tools not available in APT (or newer versions)
# ------------------------------------------------------------
install_pip_tools() {
    log "Installing pip packages (bloodhound-python, ldapdomaindump, wfuzz, arjun)..."

    pip3 install \
        --break-system-packages \
        bloodhound \
        ldapdomaindump \
        wfuzz \
        arjun \
        2>&1 | tee -a "${LOGFILE}" || warn "Some pip packages failed — check log."

    log "pip packages installed."
}

# ------------------------------------------------------------
# Kerbrute — download from GitHub (not in APT)
# ------------------------------------------------------------
install_kerbrute() {
    log "Downloading Kerbrute from GitHub..."

    local kerb_url="https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64"
    local kerb_bin="/usr/local/bin/kerbrute"

    if [[ -f "$kerb_bin" ]]; then
        info "Kerbrute already installed at ${kerb_bin}."
        return
    fi

    if wget -q -O /tmp/kerbrute_linux_amd64 "$kerb_url"; then
        chmod +x /tmp/kerbrute_linux_amd64
        mv /tmp/kerbrute_linux_amd64 "$kerb_bin"
        log "Kerbrute installed to ${kerb_bin}"
    else
        warn "Failed to download Kerbrute from latest, trying v1.0.3..."
        if wget -q -O /tmp/kerbrute_linux_amd64 \
            "https://github.com/ropnop/kerbrute/releases/download/v1.0.3/kerbrute_linux_amd64"; then
            chmod +x /tmp/kerbrute_linux_amd64
            mv /tmp/kerbrute_linux_amd64 "$kerb_bin"
            log "Kerbrute v1.0.3 installed to ${kerb_bin}"
        else
            warn "Failed to download Kerbrute. Install manually later:"
            warn "  wget https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64"
            warn "  chmod +x kerbrute_linux_amd64 && sudo mv kerbrute_linux_amd64 /usr/local/bin/kerbrute"
        fi
    fi

    # Also install netexec via pipx for latest version
    log "Installing NetExec through pipx..."
    pipx ensurepath
    pipx install git+https://github.com/Pennyw0rth/NetExec --force 2>&1 | tee -a "${LOGFILE}" || true
}

# ------------------------------------------------------------
extract_rockyou() {
    local rock="/usr/share/wordlists/rockyou.txt.gz"

    if [[ -f "$rock" ]]; then
        if [[ ! -f "/usr/share/wordlists/rockyou.txt" ]]; then
            log "Extracting rockyou.txt..."
            gunzip -k "$rock"
        else
            info "rockyou.txt is already extracted."
        fi
    else
        warn "rockyou.txt.gz not found. Skipping."
    fi
}

# ------------------------------------------------------------
clone_tools() {
    mkdir -p "$TOOLS_DIR" "$STAGE_DIR"
    cd "$TOOLS_DIR"

    if [[ ! -d PEASS-ng/.git ]]; then
        log "Cloning PEASS-ng..."
        git clone --depth 1 https://github.com/peass-ng/PEASS-ng.git
    else
        info "PEASS-ng already exists — updating..."
        cd PEASS-ng && git pull && cd ..
    fi

    log "Downloading LinPEAS.sh..."
    wget -q -O linpeas.sh \
        "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh" \
        2>/dev/null && chmod +x linpeas.sh \
        || warn "Failed to download linpeas.sh"

    log "Downloading winPEASx64.exe..."
    wget -q -O winPEASx64.exe \
        "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx64.exe" \
        2>/dev/null || warn "Failed to download winPEASx64.exe"

    log "Downloading winPEASx86.exe..."
    wget -q -O winPEASx86.exe \
        "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx86.exe" \
        2>/dev/null || warn "Failed to download winPEASx86.exe"

    if [[ ! -d SecLists/.git ]]; then
        log "Cloning SecLists..."
        git clone --depth 1 https://github.com/danielmiessler/SecLists.git
    else
        cd SecLists && git pull && cd ..
    fi

    if [[ ! -d PayloadsAllTheThings/.git ]]; then
        log "Cloning PayloadsAllTheThings..."
        git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings.git
    else
        cd PayloadsAllTheThings && git pull && cd ..
    fi

    if [[ ! -d LinEnum/.git ]]; then
        log "Cloning LinEnum..."
        git clone --depth 1 https://github.com/rebootuser/LinEnum.git
    fi

    if [[ ! -d linux-smart-enumeration/.git ]]; then
        log "Cloning linux-smart-enumeration (lse)..."
        git clone --depth 1 https://github.com/diego-treitos/linux-smart-enumeration.git
    fi

    if [[ ! -d linux-exploit-suggester/.git ]]; then
        log "Cloning Linux Exploit Suggester..."
        git clone --depth 1 https://github.com/The-Z-Labs/linux-exploit-suggester.git
    else
        cd linux-exploit-suggester && git pull && cd ..
    fi

    if [[ ! -d pspy/.git ]]; then
        log "Cloning pspy..."
        git clone --depth 1 https://github.com/DominicBreuker/pspy.git
    fi

    if [[ ! -d wesng/.git ]]; then
        log "Cloning WES-NG (Windows Exploit Suggester)..."
        git clone --depth 1 https://github.com/bitsadmin/wesng.git
    fi

    if [[ ! -d PowerSploit/.git ]]; then
        log "Cloning PowerSploit..."
        git clone --depth 1 https://github.com/PowerShellMafia/PowerSploit.git
    fi

    if [[ ! -d impacket/.git ]]; then
        log "Cloning Impacket..."
        git clone --depth 1 https://github.com/fortra/impacket.git
    else
        cd impacket && git pull && cd ..
    fi

    if [[ ! -d PKINITtools/.git ]]; then
        log "Cloning PKINITtools..."
        git clone --depth 1 https://github.com/dirkjanm/PKINITtools.git
    fi

    if [[ ! -d fuzzdb/.git ]]; then
        log "Cloning fuzzdb..."
        git clone --depth 1 https://github.com/fuzzdb-project/fuzzdb.git
    fi

    if [[ ! -d IntruderPayloads/.git ]]; then
        log "Cloning IntruderPayloads..."
        git clone --depth 1 https://github.com/1N3/IntruderPayloads.git
    fi

    if [[ ! -d static-binaries/.git ]]; then
        log "Cloning static-binaries..."
        git clone --depth 1 https://github.com/andrew-d/static-binaries.git
    fi

    if [[ ! -d SUID3NUM/.git ]]; then
        log "Cloning SUID3NUM..."
        git clone --depth 1 https://github.com/Anon-Exploiter/SUID3NUM.git
    fi

    cd "$SCRIPT_DIR"
    log "Tools cloned to: ${TOOLS_DIR}"
}

# ------------------------------------------------------------
download_static_bins() {
    local psdir="${TOOLS_DIR}/pspy"

    if [[ -d "$psdir" ]]; then
        log "Downloading precompiled pspy binaries..."
        cd "$psdir"

        for arch in amd64 arm64; do
            wget -q -O "pspy64_${arch}" \
                "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64_${arch}" \
                2>/dev/null || true

            chmod +x "pspy64_${arch}" 2>/dev/null || true
        done

        cd "$SCRIPT_DIR"
    fi
}

# ------------------------------------------------------------
# Shell configuration (Zsh) and aliases
# ------------------------------------------------------------
configure_shell() {
    local user_home="/home/kali"
    local shell_rc="${user_home}/.zshrc"
    local shell_d="${user_home}/.zshrc.d"
    local commands_file="${shell_d}/commands"
    local source_line='for f in ~/.zshrc.d/*; do [[ -f "$f" ]] && source "$f"; done'

    log "Configuring Zsh — aliases and modular .zshrc.d..."
    mkdir -p "$shell_d"

    cat > "$commands_file" << 'EOF'
# === Kali Restore — user aliases ===
alias htb='cd /home/kali/Desktop/htb'
alias hs='sudo nano /etc/hosts'
alias nmap-all='sudo nmap -p- -sV -sC -O -T4'
alias enum4='enum4linux -a'
alias smb='smbclient -L \\\\'
alias mkdir='mkdir -p'
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
EOF

    chown kali:kali "$commands_file"
    chmod 644 "$commands_file"
    log "Aliases saved to: ${commands_file}"

    if ! grep -qF "source ~/.zshrc.d/" "$shell_rc" 2>/dev/null && \
       ! grep -qF "for f in ~/.zshrc.d/" "$shell_rc" 2>/dev/null; then

        log "Adding source ~/.zshrc.d/* to ${shell_rc}..."

        {
            echo ""
            echo "# === Kali Restore — modular aliases source ==="
            echo "$source_line"
        } >> "$shell_rc"
    else
        info "Source for .zshrc.d already exists in ${shell_rc}."
    fi

    chown kali:kali "$shell_rc"
    log "Zsh shell configured."
}

# ------------------------------------------------------------
# NOPASSWD for the sudo group
# ------------------------------------------------------------
configure_sudo_nopasswd() {
    log "Configuring NOPASSWD for the sudo group..."

    cp -a /etc/sudoers "/etc/sudoers.kali-restore-backup" 2>/dev/null || true

    if grep -qP '^%sudo\s+ALL=\(ALL:ALL\)\s+NOPASSWD:\s*ALL' /etc/sudoers 2>/dev/null; then
        info "NOPASSWD for the sudo group is already configured."
        return
    fi

    if grep -qP '^%sudo\s+ALL=\(ALL:ALL\)\s+ALL' /etc/sudoers 2>/dev/null; then
        sed -i -E \
            's/^%sudo[[:space:]]+ALL=\(ALL:ALL\)[[:space:]]+ALL/#&  # commented out by kali-restore.sh/' \
            /etc/sudoers

        log "Commented out the default %sudo rule requiring a password."
    fi

    sed -i \
        '/^@includedir/i\%sudo ALL=(ALL:ALL) NOPASSWD: ALL  # added by kali-restore.sh' \
        /etc/sudoers

    if visudo -c -f /etc/sudoers 2>/dev/null; then
        log "NOPASSWD for the sudo group — configured successfully."
    else
        err "Syntax error in /etc/sudoers! Restoring backup..."
        cp -a /etc/sudoers.kali-restore-backup /etc/sudoers 2>/dev/null || true
        chmod 440 /etc/sudoers
        warn "Changes to sudoers have been reverted."
    fi
}

# ------------------------------------------------------------
# Remove empty lines from /etc/hosts
# ------------------------------------------------------------
clean_hosts_file() {
    log "Removing empty lines from /etc/hosts..."

    if [[ -f /etc/hosts ]]; then
        sed -i '/^[[:space:]]*$/d' /etc/hosts
        log "/etc/hosts cleaned."
    else
        warn "/etc/hosts not found."
    fi
}

# ------------------------------------------------------------
# Power management and screen configuration
# ------------------------------------------------------------
configure_power_management() {
    local user_home="/home/kali"
    local local_bin="${user_home}/.local/bin"
    local power_script="${local_bin}/kali-power-settings.sh"
    local autostart_dir="${user_home}/.config/autostart"
    local autostart_file="${autostart_dir}/kali-power-settings.desktop"

    log "Configuring power management and screen settings..."

    mkdir -p "$local_bin" "$autostart_dir"

    cat > "$power_script" << 'EOF'
#!/usr/bin/env bash

if command -v xset >/dev/null 2>&1; then
    xset s off
    xset s noblank
    xset -dpms
fi

if command -v xfconf-query >/dev/null 2>&1; then
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-enabled --create -t bool -s false 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/blank-on-ac --create -t int -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/blank-on-battery --create -t int -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-on-ac-sleep --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-on-ac-off --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-on-battery-sleep --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-on-battery-off --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-ac --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-battery --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-sleep-mode-on-ac --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-sleep-mode-on-battery --create -t uint -s 0 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/profile-on-ac --create -t string -s performance 2>/dev/null || true
    xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/profile-on-battery --create -t string -s performance 2>/dev/null || true
fi

if command -v xfconf-query >/dev/null 2>&1; then
    xfconf-query -c xfce4-screensaver -p /saver/enabled --create -t bool -s false 2>/dev/null || true
    xfconf-query -c xfce4-screensaver -p /saver/idle-activation/enabled --create -t bool -s false 2>/dev/null || true
    xfconf-query -c xfce4-screensaver -p /lock/enabled --create -t bool -s false 2>/dev/null || true
    xfconf-query -c xfce4-screensaver -p /lock/saver-activation/enabled --create -t bool -s false 2>/dev/null || true
    xfconf-query -c xfce4-screensaver -p /lock/sleep-activation --create -t bool -s false 2>/dev/null || true
fi

if command -v powerprofilesctl >/dev/null 2>&1; then
    powerprofilesctl set performance 2>/dev/null || true
fi

exit 0
EOF

    chmod +x "$power_script"
    chown kali:kali "$power_script"

    cat > "$autostart_file" << EOF
[Desktop Entry]
Type=Application
Name=Kali Restore Power Settings
Comment=Disable screen blanking and power saving
Exec=${power_script}
Terminal=false
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF

    chmod 644 "$autostart_file"
    chown kali:kali "$autostart_file"

    log "Power management configuration created."
}

# ------------------------------------------------------------
# Configure xrdp to prefer RFX over H.264
# ------------------------------------------------------------
configure_xrdp() {
    local gfx_config="/etc/xrdp/gfx.toml"
    local backup_config="/etc/xrdp/gfx.toml.kali-restore-backup"

    if [[ ! -f "$gfx_config" ]]; then
        warn "xrdp GFX configuration not found at ${gfx_config}. Skipping."
        return
    fi

    log "Configuring xrdp to prefer RFX over H.264..."

    if [[ ! -f "$backup_config" ]]; then
        cp -a "$gfx_config" "$backup_config"
        log "Created xrdp GFX backup: ${backup_config}"
    else
        info "xrdp GFX backup already exists: ${backup_config}"
    fi

    if grep -qE '^[[:space:]]*order[[:space:]]*=[[:space:]]*\[[[:space:]]*"H\.264",[[:space:]]*"RFX"[[:space:]]*\]' "$gfx_config"; then
        sed -i \
            's/order = \[ "H\.264", "RFX" \]/order = [ "RFX", "H.264" ]/' \
            "$gfx_config"

        log "xrdp codec order changed to RFX -> H.264."
    elif grep -qE '^[[:space:]]*order[[:space:]]*=[[:space:]]*\[[[:space:]]*"RFX",[[:space:]]*"H\.264"[[:space:]]*\]' "$gfx_config"; then
        info "xrdp already prefers RFX over H.264."
    else
        warn "Could not find the expected codec order in ${gfx_config}."
        warn "Check the file manually before changing it."
        return
    fi

    if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files xrdp.service >/dev/null 2>&1; then
        systemctl restart xrdp
        log "xrdp restarted successfully."
    else
        warn "xrdp service not found. Configuration was changed, but xrdp was not restarted."
    fi

    if grep -qE '^[[:space:]]*order[[:space:]]*=[[:space:]]*\[[[:space:]]*"RFX",[[:space:]]*"H\.264"[[:space:]]*\]' "$gfx_config"; then
        log "xrdp GFX configuration verified: RFX -> H.264."
    else
        warn "xrdp GFX configuration verification failed."
    fi
}

# ------------------------------------------------------------
# Apply graphical settings to the current session
# ------------------------------------------------------------
apply_graphical_configuration_now() {
    local panel_pid
    local display=""
    local xauthority=""
    local dbus_address=""
    local runtime_dir="/run/user/$(id -u kali)"
    local power_script="/home/kali/.local/bin/kali-power-settings.sh"

    panel_pid="$(pgrep -u kali -x xfce4-panel | head -n 1 || true)"

    if [[ -z "$panel_pid" ]]; then
        info "No active Xfce panel detected."
        info "Graphical configuration will be applied automatically at next login."
        return
    fi

    while IFS= read -r -d '' entry; do
        case "$entry" in
            DISPLAY=*)
                display="${entry#DISPLAY=}"
                ;;
            XAUTHORITY=*)
                xauthority="${entry#XAUTHORITY=}"
                ;;
            DBUS_SESSION_BUS_ADDRESS=*)
                dbus_address="${entry#DBUS_SESSION_BUS_ADDRESS=}"
                ;;
        esac
    done < "/proc/${panel_pid}/environ"

    if [[ -z "$display" ]]; then
        info "Could not determine the X display."
        info "Graphical configuration will be applied automatically at next login."
        return
    fi

    log "Applying graphical configuration to the current Xfce session..."

    local -a env_cmd=(
        env
        "DISPLAY=${display}"
        "XAUTHORITY=${xauthority:-/home/kali/.Xauthority}"
        "XDG_RUNTIME_DIR=${runtime_dir}"
    )

    if [[ -n "$dbus_address" ]]; then
        env_cmd+=("DBUS_SESSION_BUS_ADDRESS=${dbus_address}")
    fi

    runuser -u kali -- "${env_cmd[@]}" "$power_script" >/dev/null 2>&1 || true

    log "Current Xfce session configuration applied."
}

# ------------------------------------------------------------
post_install_symlinks() {
    log "Creating symbolic links for convenience..."

    mkdir -p "${TOOLS_DIR}/bin"

    ln -sf "${TOOLS_DIR}/linpeas.sh" \
        "${TOOLS_DIR}/bin/linpeas" 2>/dev/null || true

    ln -sf /usr/share/seclists \
        "${TOOLS_DIR}/seclists-link" 2>/dev/null || true
}

# ------------------------------------------------------------
summary() {
    cat << EOF

╔══════════════════════════════════════════════════════╗
║               ✓ KALI RESTORE COMPLETED              ║
╚══════════════════════════════════════════════════════╝

  Installed APT tools:
    seclists, netexec, bloodhound, ffuf, chisel,
    ligolo-ng, responder, evil-winrm, gobuster,
    impacket-scripts, metasploit, sqlmap and more.

  pip packages:
    bloodhound (bloodhound-python), ldapdomaindump,
    wfuzz, arjun

  Downloaded:
    Kerbrute -> /usr/local/bin/kerbrute

  Cloned repositories (${TOOLS_DIR}):
    PEASS-ng (linpeas + winpeas), SecLists
    PayloadsAllTheThings, LinEnum, lse
    Linux Exploit Suggester, pspy, WES-NG
    PowerSploit, Impacket, PKINITtools
    fuzzdb, IntruderPayloads, static-binaries, SUID3NUM

  Files:
    linpeas.sh, winPEASx64.exe, winPEASx86.exe
    rockyou.txt (extracted)

  Shell:
    ~/.zshrc.d/commands
    htb, hs, nmap-all, enum4, smb, ...

  Sudo:
    %sudo NOPASSWD: ALL

  /etc/hosts:
    cleaned

  Xfce:
    power management / screen blanking configured

  xrdp:
    RFX preferred over H.264
    Config: /etc/xrdp/gfx.toml
    Backup: /etc/xrdp/gfx.toml.kali-restore-backup

  Log:
    ${LOGFILE}

EOF
}

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
check_root

echo ""
info "============================================"
info "  Kali Restore $(date)"
info "  Tools dir : ${TOOLS_DIR}"
info "============================================"
echo ""

install_apt_pkgs
install_kerbrute
install_pip_tools
extract_rockyou
clone_tools
download_static_bins
configure_shell
configure_sudo_nopasswd
clean_hosts_file
configure_power_management
configure_xrdp
apply_graphical_configuration_now
post_install_symlinks
summary

log "Done! Everything has been restored."
