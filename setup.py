"""
setup.py — Install dependencies and verify the environment.
Run this once before running main.py.

Usage:
    python setup.py
"""

import sys
import subprocess
import os


REQUIRED = ["customtkinter", "watchdog", "Pillow"]


def check_python():
    if sys.version_info < (3, 8):
        print("❌  Python 3.8 or higher is required.")
        sys.exit(1)
    print(f"✅  Python {sys.version.split()[0]}")


def install_packages():
    print("\nInstalling dependencies…")
    req = os.path.join(os.path.dirname(__file__), "requirements.txt")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅  All packages installed.")
    else:
        print("⚠️   Some packages may not have installed cleanly:")
        print(result.stderr[-500:])


def verify_imports():
    print("\nVerifying imports…")
    ok = True
    for pkg in REQUIRED:
        try:
            __import__(pkg.lower().replace("-", "_"))
            print(f"  ✅  {pkg}")
        except ImportError:
            print(f"  ❌  {pkg} — install failed")
            ok = False
    return ok


def create_dirs():
    dirs = ["reports", "core", "gui", "gui/pages"]
    for d in dirs:
        os.makedirs(os.path.join(os.path.dirname(__file__), d), exist_ok=True)
    print("✅  Directories ready.")


if __name__ == "__main__":
    print("=" * 50)
    print("  FIM System — Setup")
    print("=" * 50)
    check_python()
    install_packages()
    create_dirs()
    ok = verify_imports()
    print()
    if ok:
        print("🎉  Setup complete! Run the app with:")
        print("    python main.py")
    else:
        print("⚠️  Fix the errors above, then run: python main.py")
