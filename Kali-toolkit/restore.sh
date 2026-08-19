#!/usr/bin/env bash
# ============================================================
# Kali Restore — script for quickly restoring tools
# after a system reset.
# Author: jumper-hash
# Run: chmod +x kali-restore.sh && sudo ./kali-restore.sh
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="${SCRIPT_DIR}/tools"
STAGE_DIR="${TOOLS_DIR}/staging"
DATE_TAG="$(date +%Y%m%d)"
LOGFILE="${TOOLS_DIR}/kali-restore-${DATE_TAG}.log"

# Colors
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
# Helper functions
# ------------------------------------------------------------
check_root() {
    if [[ $EUID -ne 0 ]]; then
        err "This script requires root privileges (sudo)."
        exit 1
    fi
}

install_apt_pkgs() {
    log "Updating package lists..."
    apt update -qq

    log "Installing APT packages..."
    apt install -y \
        seclists \
        wordlist \
        enum4linux \
        smbclient \
        smbmap \
        impacket-scripts \
        netexec \
        bloodhound \
        bloodhound-python \
        ldapdomaindump \
        kerbrute \
        chisel \
        ligolo-ng \
        ffuf \
        gobuster \
        dirb \
        nikto \
        wpscan \
        evil-winrm \
        hydra \
        john \
        hashcat \
        metasploit-framework \
        sqlmap \
        burpsuite \
        wireshark \
        responder \
        mitm6 \
        bettercap \
        exploitdb \
        jq \
        netcat-openbsd \
        ncat \
        tmux \
        rlwrap \
        xclip \
        python3-venv \
        python3-pip \
        bat \
        fzf \
        pipx 2>&1 | tee -a "${LOGFILE}"

    log "Installing tools through pipx..."
    pipx ensurepath

    pipx install \
        git+https://github.com/Pennyw0rth/NetExec \
        --force 2>&1 | tee -a "${LOGFILE}"
}

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

clone_tools() {
    mkdir -p "$TOOLS_DIR" "$STAGE_DIR"
    cd "$TOOLS_DIR"

    if [[ ! -d PEASS-ng/.git ]]; then
        log "Cloning PEASS-ng..."
        git clone --depth 1 \
            https://github.com/peass-ng/PEASS-ng.git
    else
        info "PEASS-ng already exists — updating..."
        cd PEASS-ng
        git pull
        cd ..
    fi

    log "Downloading LinPEAS.sh..."
    wget -q -O linpeas.sh \
        "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh" \
        2>/dev/null \
        && chmod +x linpeas.sh \
        || warn "Failed to download linpeas.sh"

    log "Downloading winPEASx64.exe..."
    wget -q -O winPEASx64.exe \
        "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx64.exe" \
        2>/dev/null \
        || warn "Failed to download winPEASx64.exe"

    log "Downloading winPEASx86.exe..."
    wget -q -O winPEASx86.exe \
        "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx86.exe" \
        2>/dev/null \
        || warn "Failed to download winPEASx86.exe"

    if [[ ! -d SecLists/.git ]]; then
        log "Cloning SecLists..."
        git clone --depth 1 \
            https://github.com/danielmiessler/SecLists.git
    else
        cd SecLists
        git pull
        cd ..
    fi

    if [[ ! -d PayloadsAllTheThings/.git ]]; then
        log "Cloning PayloadsAllTheThings..."
        git clone --depth 1 \
            https://github.com/swisskyrepo/PayloadsAllTheThings.git
    else
        cd PayloadsAllTheThings
        git pull
        cd ..
    fi

    if [[ ! -d LinEnum/.git ]]; then
        log "Cloning LinEnum..."
        git clone --depth 1 \
            https://github.com/rebootuser/LinEnum.git
    fi

    if [[ ! -d linux-smart-enumeration/.git ]]; then
        log "Cloning linux-smart-enumeration (lse)..."
        git clone --depth 1 \
            https://github.com/diego-treitos/linux-smart-enumeration.git
    fi

    if [[ ! -d linux-exploit-suggester/.git ]]; then
        log "Cloning Linux Exploit Suggester..."
        git clone --depth 1 \
            https://github.com/The-Z-Labs/linux-exploit-suggester.git
    else
        cd linux-exploit-suggester
        git pull
        cd ..
    fi

    if [[ ! -d pspy/.git ]]; then
        log "Cloning pspy..."
        git clone --depth 1 \
            https://github.com/DominicBreuker/pspy.git
    fi

    if [[ ! -d wesng/.git ]]; then
        log "Cloning WES-NG (Windows Exploit Suggester)..."
        git clone --depth 1 \
            https://github.com/bitsadmin/wesng.git
    fi

    if [[ ! -d PowerSploit/.git ]]; then
        log "Cloning PowerSploit..."
        git clone --depth 1 \
            https://github.com/PowerShellMafia/PowerSploit.git
    fi

    if [[ ! -d impacket/.git ]]; then
        log "Cloning Impacket..."
        git clone --depth 1 \
            https://github.com/fortra/impacket.git
    else
        cd impacket
        git pull
        cd ..
    fi

    if [[ ! -d PKINITtools/.git ]]; then
        log "Cloning PKINITtools..."
        git clone --depth 1 \
            https://github.com/dirkjanm/PKINITtools.git
    fi

    if [[ ! -d ldapdomaindump/.git ]]; then
        log "Cloning ldapdomaindump..."
        git clone --depth 1 \
            https://github.com/dirkjanm/ldapdomaindump.git
    fi

    if [[ ! -d fuzzdb/.git ]]; then
        log "Cloning fuzzdb..."
        git clone --depth 1 \
            https://github.com/fuzzdb-project/fuzzdb.git
    fi

    if [[ ! -d IntruderPayloads/.git ]]; then
        log "Cloning IntruderPayloads..."
        git clone --depth 1 \
            https://github.com/1N3/IntruderPayloads.git
    fi

    if [[ ! -d static-binaries/.git ]]; then
        log "Cloning static-binaries..."
        git clone --depth 1 \
            https://github.com/andrew-d/static-binaries.git
    fi

    if [[ ! -d SUID3NUM/.git ]]; then
        log "Cloning SUID3NUM..."
        git clone --depth 1 \
            https://github.com/Anon-Exploiter/SUID3NUM.git
    fi

    cd "$SCRIPT_DIR"

    log "Tools cloned to: ${TOOLS_DIR}"
}

pip_installs() {
    log "Installing Python fuzzing tools..."
    pip3 install wfuzz arjun 2>&1 | tee -a "${LOGFILE}"
}

download_static_bins() {
    local psdir="${TOOLS_DIR}/pspy"

    if [[ -d "$psdir" ]]; then
        log "Downloading precompiled pspy binaries..."

        cd "$psdir"

        for arch in amd64 arm64; do
            wget -q -O "pspy64_${arch}" \
                "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64_${arch}" \
                2>/dev/null || true
        done

        cd "$SCRIPT_DIR"
    fi
}

# === NEW SECTION: Shell configuration (Zsh) and aliases ===
configure_shell() {
    local user_home="/home/kali"
    local shell_rc="${user_home}/.zshrc"
    local shell_d="${user_home}/.zshrc.d"
    local commands_file="${shell_d}/commands"
    local source_line='for f in ~/.zshrc.d/*; do [[ -f "$f" ]] && source "$f"; done'

    log "Configuring Zsh — aliases and modular .zshrc.d..."

    # Make sure the directory and file exist
    mkdir -p "$shell_d"

    # === NEW SECTION: Aliases ===
    cat > "$commands_file" << 'EOF'
# === Kali Restore — user aliases ===

# HTB — quick jump to the directory
alias htb='cd /home/kali/Desktop/htb'

# Edit /etc/hosts with sudo (without having to enter a password)
alias hs='sudo nano /etc/hosts'

# Additional useful aliases for pentesters
alias nmap-all='sudo nmap -p- -sV -sC -O -T4'
alias enum4='enum4linux -a'
alias smb='smbclient -L \\\\\\\\'
alias mkdir='mkdir -p'
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
EOF

    chown kali:kali "$commands_file"
    chmod 644 "$commands_file"

    log "Aliases saved to: ${commands_file}"

    # Add source to .zshrc if it does not already exist
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

# === NEW SECTION: NOPASSWD for the sudo group ===
configure_sudo_nopasswd() {
    log "Configuring NOPASSWD for the sudo group..."

    # Check whether a NOPASSWD entry for %sudo already exists
    if grep -qP '^%sudo\s+ALL=\(ALL\:ALL\)\s+NOPASSWD:\s*ALL' \
        /etc/sudoers 2>/dev/null; then

        info "NOPASSWD for the sudo group is already configured."
        return
    fi

    # If a line requiring a password exists (%sudo ... ALL), comment it out
    # and add the NOPASSWD rule below
    if grep -qP '^%sudo\s+ALL=\(ALL\:ALL\)\s+ALL' \
        /etc/sudoers 2>/dev/null; then

        sed -i \
            's/^%sudo\s\+ALL=(ALL\:ALL)\s\+ALL/#\0  # commented out by kali-restore.sh/' \
            /etc/sudoers

        log "Commented out the default %sudo rule requiring a password."
    fi

    # Add the NOPASSWD rule before @includedir so that it is honored
    sed -i \
        '/^@includedir/i\%sudo ALL=(ALL\:ALL) NOPASSWD: ALL  # added by kali-restore.sh' \
        /etc/sudoers

    # Validate sudoers syntax
    if visudo -c -f /etc/sudoers 2>/dev/null; then
        log "NOPASSWD for the sudo group — configured successfully."
    else
        err "Syntax error in /etc/sudoers! Reverting..."

        # Revert changes — restore from backup if one exists
        sed -i '/# added by kali-restore.sh/d' /etc/sudoers
        sed -i \
            's/^#\(%sudo\s\+ALL=(ALL\:ALL)\s\+ALL\).*$/\1/' \
            /etc/sudoers

        warn "Changes to sudoers have been reverted. Check manually."
    fi
}

post_install_symlinks() {
    log "Creating symbolic links for convenience..."

    mkdir -p "${TOOLS_DIR}/bin"

    ln -sf \
        "${TOOLS_DIR}/linpeas.sh" \
        "${TOOLS_DIR}/bin/linpeas" \
        2>/dev/null || true

    ln -sf \
        /usr/share/seclists \
        "${TOOLS_DIR}/seclists-link" \
        2>/dev/null || true
}

summary() {
    cat << EOF

╔══════════════════════════════════════════════════════╗
║               ✓ KALI RESTORE COMPLETED              ║
╚══════════════════════════════════════════════════════╝

  Installed APT tools:
    seclists, netexec, bloodhound, ffuf, chisel,
    ligolo-ng, responder, evil-winrm, gobuster,
    impacket-scripts, metasploit, sqlmap and more.

  Cloned repositories (${TOOLS_DIR}):
    PEASS-ng (linpeas + winpeas)
    SecLists
    PayloadsAllTheThings
    LinEnum, linux-smart-enumeration
    Linux Exploit Suggester
    pspy
    WES-NG, PowerSploit
    Impacket, PKINITtools, ldapdomaindump
    fuzzdb, IntruderPayloads
    static-binaries
    SUID3NUM

  Files:
    linpeas.sh, winPEASx64.exe, winPEASx86.exe
    rockyou.txt (extracted)

  Additional: wfuzz, arjun (pip3)

  Shell: ~/.zshrc.d/commands with aliases (htb, hs)
  Sudo:  %sudo NOPASSWD: ALL

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
extract_rockyou
clone_tools
pip_installs
download_static_bins

# === NEW FUNCTION CALLS ===
configure_shell
configure_sudo_nopasswd

post_install_symlinks
summary

log "Done! Everything has been restored."
