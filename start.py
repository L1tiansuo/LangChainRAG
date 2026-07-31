"""RAG System Launcher - One-click start script."""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_DIR / "backend"
FRONTEND_DIR = PROJECT_DIR / "frontend"
DB_PATH = BACKEND_DIR / "data" / "app.db"
PID_FILE = PROJECT_DIR / ".pids.txt"


def check_tool(check_cmd: str) -> bool:
    """Check if a command-line tool is available."""
    try:
        subprocess.run(check_cmd, shell=True, capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def start_in_new_window(title: str, cwd: Path, *args: str) -> None:
    """Launch a command in a new console window.

    Uses CREATE_NEW_CONSOLE for a visible window. The window title
    is set via a batch wrapper to avoid quoting issues with start.
    """
    import tempfile

    # Write a tiny batch script that sets the title then runs the command
    bat = tempfile.NamedTemporaryFile(
        mode="w", suffix=".bat", delete=False, encoding="utf-8"
    )
    bat.write(f"@echo off\n")
    bat.write(f"title {title}\n")
    bat.write(f"cd /d {cwd}\n")
    bat.write(" ".join(args) + "\n")
    bat.write("pause\n")
    bat.close()

    subprocess.Popen(
        [bat.name],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def main():
    print("=" * 50)
    print("  RAG 企业知识库问答系统 - 启动")
    print("=" * 50)
    print(f"  项目目录: {PROJECT_DIR}")
    print()

    # ── Step 1: Checks ──
    print("[1/4] 检查环境...")
    if not check_tool("python --version"):
        print("[错误] 未找到 Python，请先安装 Python 3.10+")
        input("按 Enter 退出...")
        sys.exit(1)
    print("       Python OK")

    if not check_tool("node --version"):
        print("[错误] 未找到 Node.js，请先安装 Node.js 18+")
        input("按 Enter 退出...")
        sys.exit(1)
    print("       Node.js OK")
    print()

    # ── Step 2: Init DB ──
    print("[2/4] 检查数据库...")
    if not DB_PATH.exists():
        print("       首次运行，正在初始化...")
        result = subprocess.run(
            [sys.executable, "init_db.py"], cwd=str(BACKEND_DIR),
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"[错误] 数据库初始化失败:\n{result.stderr}")
            input("按 Enter 退出...")
            sys.exit(1)
        print("       数据库初始化完成!")
    else:
        print("       数据库已存在，跳过。")
    print()

    # ── Step 3: Install deps ──
    print("[3/4] 检查依赖...")
    if not (FRONTEND_DIR / "node_modules").exists():
        print("       正在安装前端依赖（首次运行，可能需要几分钟）...")
        result = subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), shell=True)
        if result.returncode != 0:
            print("[错误] 前端依赖安装失败!")
            input("按 Enter 退出...")
            sys.exit(1)
        print("       依赖安装完成!")
    else:
        print("       前端依赖已就绪。")
    print()

    # ── Step 4: Start ──
    print("[4/4] 启动服务...")
    print()

    # Start backend
    print("启动后端服务...")
    start_in_new_window("RAG-Backend", BACKEND_DIR, sys.executable, "run.py")

    # Wait for backend
    print("等待后端就绪...")
    import urllib.request, urllib.error
    for _ in range(20):
        time.sleep(2)
        try:
            resp = urllib.request.urlopen("http://localhost:8000/health", timeout=2)
            if resp.status == 200:
                print("后端已就绪!")
                break
        except (urllib.error.URLError, OSError):
            print(".", end="", flush=True)
    print()

    # Start frontend
    print("启动前端服务...")
    start_in_new_window("RAG-Frontend", FRONTEND_DIR, "npm", "run", "dev")

    time.sleep(5)
    print("前端已就绪!")
    print()

    # Open browser
    print("正在打开浏览器...")
    webbrowser.open("http://localhost:5173")

    print()
    print("=" * 50)
    print("  启动完成!")
    print()
    print("   前端页面 : http://localhost:5173")
    print("   后端 API : http://localhost:8000")
    print("   API 文档 : http://localhost:8000/docs")
    print()
    print("   管理员账号 : admin")
    print("   管理员密码 : 123456")
    print("=" * 50)
    print()
    try:
        input("按 Enter 退出此窗口（服务将继续运行）...")
    except (EOFError, OSError):
        pass


if __name__ == "__main__":
    main()
