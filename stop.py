"""Stop RAG services — kill only processes on RAG ports (8000, 5173)."""

import subprocess

RAG_PORTS = ["8000", "5173", "5174", "5175"]


def get_pid_on_port(port: str) -> str | None:
    """Get the PID listening on a given port via PowerShell."""
    result = subprocess.run(
        ["powershell", "-Command",
         f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
         f"Select-Object -First 1 -ExpandProperty OwningProcess) -join ''"],
        capture_output=True, text=True,
    )
    pid = result.stdout.strip()
    return pid if pid and pid != "0" else None


def kill_pid(pid: str) -> bool:
    """Kill a process tree by PID."""
    r = subprocess.run(
        ["taskkill", "/F", "/T", "/PID", pid],
        capture_output=True, text=True, shell=True,
    )
    return r.returncode == 0


def main():
    print("=" * 40)
    print("  Stopping RAG services...")
    print("=" * 40)

    killed = 0
    for port in RAG_PORTS:
        pid = get_pid_on_port(port)
        if pid:
            kill_pid(pid)
            print(f"  Stopped PID {pid} (port {port})")
            killed += 1

    if killed == 0:
        print("  No RAG services found running.")
    else:
        print()
        print(f"  Stopped {killed} process(es).")

    print("  Other Python/Node programs unaffected.")
    print("=" * 40)


if __name__ == "__main__":
    main()
