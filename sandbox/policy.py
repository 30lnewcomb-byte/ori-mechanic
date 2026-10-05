import shlex

# Small, intentionally boring allowlist. Expand only when a real repair workflow
# needs another command.
ALLOWED_COMMANDS = {
    "python",
    "python3",
    "pip",
    "pytest",
    "git",
    "node",
    "npm",
}

BLOCKED_TOKENS = {
    "sudo", "su", "mount", "umount", "docker", "podman",
    "systemctl", "service", "shutdown", "reboot",
    "mkfs", "fdisk", "iptables", "nft", "curl", "wget",
}

def validate_command(command: str) -> tuple[bool, str]:
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return False, f"invalid command syntax: {exc}"

    if not parts:
        return False, "empty command"

    executable = parts[0].split("/")[-1]
    if executable not in ALLOWED_COMMANDS:
        return False, f"command '{executable}' is not allowlisted"

    lowered = command.lower()
    for token in BLOCKED_TOKENS:
        if token in lowered:
            return False, f"blocked token: {token}"

    return True, ""
