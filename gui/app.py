import tkinter as tk
from utils.icon import apply_window_icon
from logic.config import load_stored_output_dir
from gui.main_gui import GalleryDLGUI
from utils.env_check import check_gallery_dl_installed, check_python_system_installed

def run_app():
    check_python_system_installed()
    check_gallery_dl_installed()
    root = tk.Tk()
    apply_window_icon(root)
    app = GalleryDLGUI(root)
    root.mainloop()