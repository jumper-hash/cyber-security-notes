#!/usr/bin/env bash
# ============================================================
# Kali Restore v 2.2
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
        xfce4-genmon-plugin power-profiles-daemon
    )

    local success=0 fail=0
    for pkg in "${apt_pkgs[@]}"; do
        if apt install -y "$pkg" &>> "${LOGFILE}"; then
            ((++success))   # <-- fixed: pre-increment
        else
            warn "Package '$pkg' not found in repos — skipping."
            ((++fail))      # <-- fixed: pre-increment
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

    # FIXED: sed -E for extended regex, proper escaping
    if grep -qP '^%sudo\s+ALL=\(ALL:ALL\)\s+ALL' /etc/sudoers 2>/dev/null; then
        sed -i -E 's/^%sudo[[:space:]]+ALL=\(ALL:ALL\)[[:space:]]+ALL/#&  # commented out by kali-restore.sh/' /etc/sudoers
        log "Commented out the default %sudo rule requiring a password."
    fi

    # Insert NOPASSWD rule before @includedir
    sed -i '/^@includedir/i\%sudo ALL=(ALL:ALL) NOPASSWD: ALL  # added by kali-restore.sh' /etc/sudoers

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
# Clean /etc/hosts status for the Xfce panel
# ------------------------------------------------------------
configure_hosts_panel() {
    local user_home="/home/kali"
    local local_bin="${user_home}/.local/bin"
    local hosts_script="${local_bin}/hosts-status.sh"
    local panel_script="${local_bin}/kali-panel-setup.sh"
    local autostart_dir="${user_home}/.config/autostart"
    local autostart_file="${autostart_dir}/kali-panel-setup.desktop"

    log "Configuring clean /etc/hosts status for the Xfce panel..."
    mkdir -p "$local_bin" "$autostart_dir"

    cat > "$hosts_script" << 'EOF'
#!/usr/bin/env bash
awk 'NF { last=$0 } END { if (last != "") print last }' /etc/hosts
EOF
    chmod +x "$hosts_script"
    chown kali:kali "$hosts_script"

    cat > "$panel_script" << 'PANELSCRIPT'
#!/usr/bin/env bash
set -u

HOSTS_SCRIPT="/home/kali/.local/bin/hosts-status.sh"

get_panel_ids() {
    xfconf-query -c xfce4-panel -l 2>/dev/null \
        | awk -F/ '$2 == "panels" && $3 ~ /^panel-[0-9]+$/ { print $3 }' \
        | sort -u
}

get_plugin_ids() {
    local panel="$1"
    xfconf-query -c xfce4-panel -p "/panels/${panel}/plugin-ids" 2>/dev/null \
        | tail -n +3
}

get_plugin_type() {
    local id="$1"
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${id}" 2>/dev/null || true
}

get_plugin_command() {
    local id="$1"
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${id}/command" 2>/dev/null || true
}

for _ in {1..30}; do
    if pgrep -u kali -x xfce4-panel >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! pgrep -u kali -x xfce4-panel >/dev/null 2>&1; then
    exit 0
fi

TARGET_PANEL=""
while IFS= read -r panel; do
    [[ -z "$panel" ]] && continue
    while IFS= read -r id; do
        [[ -z "$id" ]] && continue
        type="$(get_plugin_type "$id")"
        if [[ "$type" == "clock" ]]; then
            TARGET_PANEL="$panel"
            break 2
        fi
    done < <(get_plugin_ids "$panel")
done < <(get_panel_ids)

[[ -z "$TARGET_PANEL" ]] && TARGET_PANEL="panel-1"

GENMON_ID=""
while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    type="$(get_plugin_type "$id")"
    if [[ "$type" == "genmon" ]]; then
        command="$(get_plugin_command "$id")"
        if [[ "$command" == "$HOSTS_SCRIPT" ]]; then
            GENMON_ID="$id"
            break
        fi
    fi
done < <(get_plugin_ids "$TARGET_PANEL")

if [[ -z "$GENMON_ID" ]]; then
    declare -A BEFORE_IDS=()
    while IFS= read -r id; do
        [[ -z "$id" ]] && continue
        BEFORE_IDS["$id"]=1
    done < <(get_plugin_ids "$TARGET_PANEL")

    xfce4-panel --add=genmon >/dev/null 2>&1 || true
    sleep 1

    while IFS= read -r id; do
        [[ -z "$id" ]] && continue
        if [[ -z "${BEFORE_IDS[$id]+x}" ]]; then
            type="$(get_plugin_type "$id")"
            if [[ "$type" == "genmon" ]]; then
                GENMON_ID="$id"
                break
            fi
        fi
    done < <(get_plugin_ids "$TARGET_PANEL")
fi

if [[ -z "$GENMON_ID" ]]; then
    exit 0
fi

xfconf-query -c xfce4-panel -p "/plugins/plugin-${GENMON_ID}/command" --create -t string -s "$HOSTS_SCRIPT" 2>/dev/null || true
xfconf-query -c xfce4-panel -p "/plugins/plugin-${GENMON_ID}/use-label" --create -t bool -s false 2>/dev/null || true
xfconf-query -c xfce4-panel -p "/plugins/plugin-${GENMON_ID}/enable-single-row" --create -t bool -s true 2>/dev/null || true
xfconf-query -c xfce4-panel -p "/plugins/plugin-${GENMON_ID}/update-period" --create -t int -s 500 2>/dev/null || true
xfconf-query -c xfce4-panel -p "/plugins/plugin-${GENMON_ID}/font" --create -t string -s "Arial 17" 2>/dev/null || true
xfconf-query -c xfce4-panel -p "/plugins/plugin-${GENMON_ID}/text" --create -t string -s "" 2>/dev/null || true

mapfile -t CURRENT_IDS < <(get_plugin_ids "$TARGET_PANEL")

CLOCK_ID=""
for id in "${CURRENT_IDS[@]}"; do
    type="$(get_plugin_type "$id")"
    if [[ "$type" == "clock" ]]; then
        CLOCK_ID="$id"
        break
    fi
done

NEW_ORDER=()
INSERTED=false
for id in "${CURRENT_IDS[@]}"; do
    [[ "$id" == "$GENMON_ID" ]] && continue
    if [[ -n "$CLOCK_ID" && "$id" == "$CLOCK_ID" && "$INSERTED" == false ]]; then
        NEW_ORDER+=("$GENMON_ID")
        INSERTED=true
    fi
    NEW_ORDER+=("$id")
done
[[ "$INSERTED" == false ]] && NEW_ORDER+=("$GENMON_ID")

XFCONF_CMD=(xfconf-query -c xfce4-panel -p "/panels/${TARGET_PANEL}/plugin-ids" -a -t int)
for id in "${NEW_ORDER[@]}"; do
    XFCONF_CMD+=(-s "$id")
done
"${XFCONF_CMD[@]}" 2>/dev/null || true

xfce4-panel -r >/dev/null 2>&1 || true
exit 0
PANELSCRIPT

    chmod +x "$panel_script"
    chown kali:kali "$panel_script"

    cat > "$autostart_file" << EOF
[Desktop Entry]
Type=Application
Name=Kali Restore Panel
Comment=Configure the /etc/hosts GenMon panel item
Exec=${panel_script}
Terminal=false
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF

    chmod 644 "$autostart_file"
    chown kali:kali "$autostart_file"
    log "Hosts status panel configuration created."
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
    local setup_script="/home/kali/.local/bin/kali-panel-setup.sh"
    local power_script="/home/kali/.local/bin/kali-power-settings.sh"

    panel_pid="$(pgrep -u kali -x xfce4-panel | head -n 1 || true)"
    if [[ -z "$panel_pid" ]]; then
        info "No active Xfce panel detected."
        info "Graphical configuration will be applied automatically at next login."
        return
    fi

    while IFS= read -r -d '' entry; do
        case "$entry" in
            DISPLAY=*)  display="${entry#DISPLAY=}"  ;;
            XAUTHORITY=*) xauthority="${entry#XAUTHORITY=}" ;;
            DBUS_SESSION_BUS_ADDRESS=*) dbus_address="${entry#DBUS_SESSION_BUS_ADDRESS=}" ;;
        esac
    done < "/proc/${panel_pid}/environ"

    if [[ -z "$display" ]]; then
        info "Could not determine the X display."
        info "Graphical configuration will be applied automatically at next login."
        return
    fi

    log "Applying graphical configuration to the current Xfce session..."

    # Build env vars and use eval to handle spaces/quoting properly
    local env_vars="DISPLAY=${display}"
    env_vars="${env_vars} XAUTHORITY=${xauthority:-/home/kali/.Xauthority}"
    env_vars="${env_vars} DBUS_SESSION_BUS_ADDRESS=${dbus_address:-}"
    env_vars="${env_vars} XDG_RUNTIME_DIR=${runtime_dir}"

    runuser -u kali -- env "${env_vars}" "$power_script" >/dev/null 2>&1 || true
    runuser -u kali -- env "${env_vars}" "$setup_script" >/dev/null 2>&1 || true

    log "Current Xfce session configuration applied."
}

# ------------------------------------------------------------
post_install_symlinks() {
    log "Creating symbolic links for convenience..."
    mkdir -p "${TOOLS_DIR}/bin"
    ln -sf "${TOOLS_DIR}/linpeas.sh" "${TOOLS_DIR}/bin/linpeas" 2>/dev/null || true
    ln -sf /usr/share/seclists "${TOOLS_DIR}/seclists-link" 2>/dev/null || true
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

  Shell: ~/.zshrc.d/commands (htb, hs, nmap-all, enum4, smb, ...)
  Sudo:  %sudo NOPASSWD: ALL
  /etc/hosts: cleaned + panel GenMon przed zegarem

  Log: ${LOGFILE}
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
install_kerbrute   # also installs netexec via pipx
install_pip_tools
extract_rockyou
clone_tools
download_static_bins
configure_shell
configure_sudo_nopasswd
clean_hosts_file
configure_power_management
configure_hosts_panel
apply_graphical_configuration_now
post_install_symlinks
summary

log "Done! Everything has been restored."
