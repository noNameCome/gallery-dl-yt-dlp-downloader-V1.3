import subprocess
import sys
from tkinter import messagebox

def check_gallery_dl_installed():
    try:
        subprocess.run(["gallery-dl", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        messagebox.showerror("gallery-dl 필요", "gallery-dl 설치 필요합니다.")
        sys.exit(1)

def check_python_system_installed():
    try:
        subprocess.check_output(["where", "python"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        messagebox.showerror("Python 필요", "Python이 시스템에 설치되어 있어야 합니다.")
        sys.exit(1)