#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当前项目的开发辅助入口。

优先服务于新的产品化架构：
- backend: FastAPI
- frontend: Vue + Vite
- worker: RQ worker
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEV_SCRIPT = ROOT / "scripts" / "dev.ps1"


COMMAND_ALIASES = {
    "all": "dev",
    "test-backend": "test-backend",
    "test-frontend": "test-frontend",
}


def print_help() -> None:
    print("RAG智能文档检索助手开发辅助入口")
    print()
    print("用法:")
    print("  python run.py [dev|all|backend|frontend|worker|stop|status|test|check|build|coverage|lint|health|smoke|clean|test-backend|test-frontend]")
    print()
    print("示例:")
    print("  python run.py dev")
    print("  python run.py backend")
    print("  python run.py test")


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "all"
    if command in {"-h", "--help", "help"}:
        print_help()
        return 0

    target = sys.argv[2] if len(sys.argv) > 2 else ""

    if command == "test-backend":
        argv = ["cmd", "/c", "scripts\\test_backend.bat"]
    elif command == "test-frontend":
        argv = ["cmd", "/c", "scripts\\test_frontend.bat"]
    else:
        resolved_command = COMMAND_ALIASES.get(command, command)
        allowed = {"dev", "backend", "frontend", "worker", "stop", "status", "test", "check", "build", "coverage", "lint", "health", "smoke", "clean"}
        if resolved_command not in allowed:
            print(f"未知命令: {command}")
            print()
            print_help()
            return 1

        argv = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(DEV_SCRIPT),
            resolved_command,
        ]
        if target:
            argv.append(target)

    if argv is None:
        print(f"未知命令: {command}")
        print()
        print_help()
        return 1

    completed = subprocess.run(argv, cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
