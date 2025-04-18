import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import json
import re
import signal
import requests
from PIL import Image
from tkinter import ttk
if sys.platform == "win32":
    os.system("chcp 65001")


from logic.config import load_stored_output_dir, store_output_dir
from logic.downloader import smart_download as ytdlp_smart_download
from logic.downloader import is_youtube
from logic.downloader import download_gallery as gallery_download
from logic.downloader import kill_proc_tree

CREATE_NO_WINDOW = 0x08000000
HACKER_GREEN = "#00FF00"
HACKER_BG = "#0d0d0d"
HACKER_DARK = "#1a1a1a"
HACKER_ACCENT = "#39FF14"
placeholder_text = "파일이름 입력 (선택)"

class GalleryDLGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("💀 gallery-dl 다운로더 by noName_Come")
        self.root.geometry("780x750")
        self.root.configure(bg=HACKER_BG)
        self.root.resizable(False, False)
        self.processes = []
        self.stored_dir = load_stored_output_dir()
        self.init_ui()

    def init_ui(self):
        self.url_var = tk.StringVar()
        font = ("Malgun Gothic", 14)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Vertical.TScrollbar",gripcount=0,background="#444444",troughcolor="#222222",bordercolor="#000000",lightcolor="#222222",darkcolor="#222222",arrowcolor="#00FF00",relief="flat",width=10)
        style.map("Custom.Vertical.TScrollbar",background=[("active", "#00aa00"), ("pressed", "#007700")])

        top_frame = tk.Frame(self.root, bg=HACKER_BG)
        top_frame.pack(padx=10, pady=15, fill="x")

        top_buttons_row = tk.Frame(top_frame, bg=HACKER_BG)
        top_buttons_row.pack()

        filename_frame = tk.Frame(self.root, bg=HACKER_BG)
        filename_frame.pack(pady=(0, 0))

        self.url_container = tk.Frame(top_frame, bg=HACKER_BG)
        self.url_container.pack(side="left", fill="both", expand=True)

        self.url_sets = []
        self.add_url_field()# 초기 한 개 필드 추가

        self.add_url_btn = tk.Button(top_buttons_row, text="+ URL", font=font,bg="#1f1f1f", fg=HACKER_GREEN, relief="flat", activebackground=HACKER_ACCENT, command=self.add_url_field)
        self.add_url_btn.pack(side="left", padx=(0, 6), ipady=3)

        self.remove_url_btn = tk.Button(top_buttons_row, text="- URL", font=font,bg="#1f1f1f", fg=HACKER_GREEN, relief="flat", activebackground=HACKER_ACCENT, command=self.remove_url_field)
        self.remove_url_btn.pack(side="left", padx=(0, 6), ipady=3)

        self.download_btn = tk.Button(top_buttons_row, text="⬇ 다운로드", font=font,width=10, bg="#1f1f1f", fg=HACKER_GREEN, relief="flat", activebackground=HACKER_ACCENT, command=self.start_download)
        self.download_btn.pack(side="left", padx=(0, 6), ipady=3)
        
        folder_row = tk.Frame(top_frame, bg=HACKER_BG)
        folder_row.pack(pady=(6, 0))

        path_frame = tk.Frame(self.root, bg=HACKER_BG)
        path_frame.pack(pady=(0, 4))

        tk.Label(path_frame, text="📁 저장 위치:", font=font, bg=HACKER_BG, fg=HACKER_GREEN).pack(side=tk.LEFT)

        self.output_dir_var = tk.StringVar(value=self.stored_dir or os.getcwd())
        self.output_entry = tk.Entry(path_frame, textvariable=self.output_dir_var, width=50,font=font, bg=HACKER_DARK, fg=HACKER_GREEN, insertbackground=HACKER_GREEN, relief="flat")
        self.output_entry.pack(side=tk.LEFT, padx=7)

        tk.Button(path_frame, text="탐색", font=font, command=self.browse_output_dir, bg="#1f1f1f", fg=HACKER_GREEN, relief="flat", activebackground=HACKER_ACCENT).pack(side=tk.LEFT, padx=(0, 5))

        self.play_btn = tk.Button(top_buttons_row, text="📂 폴더 열기", font=font, command=self.open_download_folder,bg="#1f1f1f", fg=HACKER_GREEN, relief="flat", activebackground=HACKER_ACCENT)
        self.play_btn.pack(side="left", padx=(0, 6), ipady=3)

        tk.Button(top_buttons_row, text="Config 열기", font=font, command=self.open_or_create_config, bg="#1f1f1f", fg=HACKER_GREEN, relief="flat", activebackground=HACKER_ACCENT).pack(side=tk.LEFT, padx=(0, 6), ipady=3)

        self.filter_vars = {ext: tk.BooleanVar() for ext in ["zip", "mp4", "jpeg", "png", "gif"]}
        filters_frame = tk.Frame(self.root, bg=HACKER_BG)
        filters_frame.pack(pady=5)
        tk.Label(filters_frame, text="다운받을 확장자 선택 (미선택시 전체 다운)", font=font, fg=HACKER_GREEN, bg=HACKER_BG).pack(side=tk.LEFT)

        # ---- yt-dlp 옵션 설정 ----
        ytdlp_frame = tk.Frame(self.root, bg=HACKER_BG)
        ytdlp_frame.pack(pady=6)

         # ---- yt-dlp 옵션 설정 ----
        separator_label = tk.Label(self.root,text="*" * 30 + " 유튜브 관련 옵션 " + "*" * 30,font=("Malgun Gothic", 14, "bold"), fg=HACKER_ACCENT, bg=HACKER_BG,anchor="center")
        separator_label.pack(pady=(10, 4))

        ytdlp_frame = tk.Frame(self.root, bg=HACKER_BG)
        ytdlp_frame.pack(pady=6)

        self.resolution_var = tk.StringVar(value="720")
        tk.Label(ytdlp_frame, text="🎥 해상도 선택:", font=font, fg=HACKER_GREEN, bg=HACKER_BG).pack(side="left", padx=(0, 8))

        for res in ["720", "1080", "1440", "2160"]:
            btn = tk.Radiobutton(ytdlp_frame, text=res, variable=self.resolution_var, value=res,font=font, bg=HACKER_BG, fg=HACKER_GREEN,selectcolor=HACKER_DARK, activebackground=HACKER_DARK, activeforeground=HACKER_GREEN)
            btn.pack(side="left", padx=5)

        self.audio_only_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ytdlp_frame, text="🎵 mp3만 저장", variable=self.audio_only_var, font=font, bg=HACKER_BG, fg=HACKER_GREEN, selectcolor=HACKER_DARK).pack(side="left")
        self.audio_only_var.trace_add("write", self.toggle_resolution_buttons)

        log_frame = tk.Frame(self.root, bg=HACKER_BG)
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.output_log = tk.Text(log_frame, width=90, height=10,font=("Malgun Gothic", 10),bg="black", fg=HACKER_GREEN,insertbackground=HACKER_GREEN,relief="flat", wrap="word")
        scrollbar = ttk.Scrollbar(log_frame,orient="vertical",command=self.output_log.yview,style="Custom.Vertical.TScrollbar")

        self.output_log.configure(yscrollcommand=scrollbar.set)
        self.output_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for ext, var in self.filter_vars.items():
            cb = tk.Checkbutton(filters_frame, text=ext, variable=var, font=font,bg=HACKER_BG, fg=HACKER_GREEN, selectcolor=HACKER_DARK,activebackground=HACKER_DARK, activeforeground=HACKER_GREEN)
            cb.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(self.root, text="⛔ 취소", font=font,bg="#FF3131", fg="black", relief="flat", command=self.cancel_download, state=tk.DISABLED)
        self.cancel_button.pack(pady=5)

        self.status_var = tk.StringVar(value="상태: 대기중")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, anchor='w',font=font, bg=HACKER_BG, fg=HACKER_GREEN)
        self.status_label.pack(fill='x', padx=10, pady=5)

    def add_url_field(self):
        row_frame = tk.Frame(self.url_container, bg=HACKER_BG)
        row_frame.pack(fill="x", pady=6)

        url_entry = tk.Entry(row_frame,font=("Malgun Gothic", 12),bg=HACKER_DARK,fg=HACKER_GREEN,insertbackground=HACKER_GREEN,relief="flat")
        url_entry.insert(0, "URL을 입력하세요")
        url_entry.pack(side="top", fill="x", padx=2, ipady=5)
        url_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(url_entry, "URL을 입력하세요"))
        url_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(url_entry, "URL을 입력하세요"))

        filename_entry = tk.Entry(row_frame,font=("Malgun Gothic", 12),bg=HACKER_DARK,fg=HACKER_GREEN,insertbackground=HACKER_GREEN,relief="flat")
        filename_entry.insert(0, "파일이름 입력 (선택)")
        filename_entry.pack(side="top", fill="x", padx=2, pady=(4, 0), ipady=3)
        filename_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(filename_entry, "파일이름 입력 (선택)"))
        filename_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(filename_entry, "파일이름 입력 (선택)"))

        self.url_sets.append((url_entry, filename_entry, row_frame))

        new_height = 750 + len(self.url_sets) * 60
        self.root.geometry(f"780x{new_height}")

    def toggle_resolution_buttons(self, *args):
        state = tk.DISABLED if self.audio_only_var.get() else tk.NORMAL
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, tk.Radiobutton) and btn.cget("text") in ["720", "1080", "1440", "2160"]:
                        btn.config(state=state)


    def remove_url_field(self):
        if len(self.url_sets) > 1:
            _, _, row_frame = self.url_sets.pop()
            row_frame.destroy()

            new_height = 750 + len(self.url_sets) * 60
            self.root.geometry(f"780x{new_height}")

    def open_download_folder(self):
        if hasattr(self, 'last_community_path') and self.last_community_path:
            folder_path = self.last_community_path
        else:
            folder_path = self.output_dir_var.get().strip()

        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("오류", f"폴더 열기 실패:\n{e}")
        else:
            messagebox.showwarning("경고", "지정한 폴더가 존재하지 않습니다.")

    def download_thread(self, url, output_dir):
        def log(msg):
            self.log_area.insert(tk.END, msg + "\n")
            self.log_area.see(tk.END)

        def cancel():
            return self._cancel_requested

        result = ytdlp_smart_download(
            url, output_dir, filename=None,
            log_func=self.thread_safe_log,
            resolution=self.resolution_var.get(),
            audio_only=self.audio_only_var.get(),
            cancel_check_func=cancel
        )

        if isinstance(result, str):
            self.last_community_path = result

        self.status_var.set("상태: 완료" if result else "상태: 실패")
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")

    def thread_safe_log(self, msg):
        self.root.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg):
        self.output_log.config(state=tk.NORMAL)
        self.output_log.insert(tk.END, msg + '\n')
        self.output_log.see(tk.END)
        self.output_log.config(state=tk.DISABLED)

    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def restore_placeholder(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)

    def download_multiple(self, url_info_list, output_dir):
        failed_urls = []

        for idx, (url, filename) in enumerate(url_info_list, start=1):
            self.status_var.set(f"상태: 다운로드 중... ({idx}/{len(url_info_list)})")
            success = self.smart_download(url, output_dir, idx, filename)

            if not success:
                self.log(f"❌ 실패: {url}")
                failed_urls.append(url)

            if failed_urls:
                self.log("🚫 다음 URL들은 실패했습니다:")
                for f in failed_urls:
                    self.log(f"    - {f}")
                self.status_var.set("상태: 일부 실패")
            else:
                self.status_var.set("상태: 완료")
                self.log("✅ 모든 다운로드 성공!")

            self.enable_ui()

    def start_download(self):
        self.resolution_warning_shown = False
        self._cancel_requested = False

        url_info = []

        for i, (url_entry, file_entry, _) in enumerate(self.url_sets, start=1):
            url = url_entry.get().strip()
            filename = file_entry.get().strip()

            if re.match(r'^https?://', url):
                if filename == "파일이름 입력 (선택)" or not filename:
                    filename = None
                url_info.append((url, filename))

        if not url_info:
            try:
                clip = self.root.clipboard_get()
                if re.match(r'^https?://', clip.strip()):
                    url_info.append((clip.strip(), None))
                else:
                    raise ValueError
            except:
                messagebox.showerror("오류", "URL을 입력하거나 클립보드에 유효한 링크가 있어야 합니다.")
                return

        output_dir = self.output_dir_var.get().strip()
        self.store_output_dir(output_dir)
        self.disable_ui()
        self.status_var.set("상태: 다운로드 중...")
        self.log("🟢 다운로드 시작...")

        threading.Thread(target=self.download_multiple, args=(url_info, output_dir)).start()

    def cancel_download(self):
        self._cancel_requested = True
        self.status_var.set("상태: 취소 요청됨")
        self.log("⛔ 취소 요청 → 모든 다운로드 중단 시도 중...")

        for proc in self.processes:
            try:
                if os.name == "nt":
                    self.log(f"⚠ 강제 종료 시도 (PID: {proc.pid})")
                    kill_proc_tree(proc.pid)  # ✅ 여기 핵심!
                else:
                    proc.terminate()
            except Exception as e:
                self.log(f"⚠️ 프로세스 종료 실패: {e}")

        self.processes.clear()
        self.enable_ui()

    def disable_ui(self):
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)

    def enable_ui(self):
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def log(self, message):
        self.output_log.config(state=tk.NORMAL)
        self.output_log.insert(tk.END, message + "\n")
        self.output_log.see(tk.END)
        self.output_log.config(state=tk.DISABLED)

    def store_output_dir(self, path):
        try:
            with open(CONFIG_STORE, 'w', encoding='utf-8') as f:
                json.dump({"last_output_dir": path}, f, indent=4)
        except:
            pass

    def load_stored_output_dir(self):
        if os.path.exists(CONFIG_STORE):
            try:
                with open(CONFIG_STORE, 'r', encoding='utf-8') as f:
                    return json.load(f).get("last_output_dir")
            except:
                return None

    def browse_output_dir(self):
        dir = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if dir:
            self.output_dir_var.set(dir)
            self.store_output_dir(dir)

    def open_or_create_config(self):
            config_path = os.path.join(os.environ.get("USERPROFILE", ""), "gallery-dl", "config.json")
            config_dir = os.path.dirname(config_path)
            os.makedirs(config_dir, exist_ok=True)
            if not os.path.exists(config_path):
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4)
            try:
                os.startfile(config_path)
            except Exception as e:
                messagebox.showerror("오류", f"config.json 열기 실패:\n{e}")    

    def smart_download(self, url, output_dir, num, filename):
        try:
            if is_youtube(url):
                resolution = self.resolution_var.get()
                audio_only = self.audio_only_var.get()

                if resolution == "화질" or resolution not in ["720", "1080", "1440", "2160"]:
                    if not self.resolution_warning_shown:
                        messagebox.showwarning("해상도 선택 필요", "⚠ 해상도를 선택해주세요!\n\n유튜브 영상 다운로드를 위해 해상도를 지정해야 합니다.")
                        self.resolution_warning_shown = True
                    self.log("⚠ 다운로드 취소: 해상도 미선택")
                    return False

                return ytdlp_smart_download(
                    url=url,
                    output_dir=output_dir,
                    filename=filename,
                    log_func=self.log,
                    resolution=resolution,
                    audio_only=audio_only,
                    cancel_check_func=lambda: self._cancel_requested
                )
            else:
                selected_exts = [ext for ext, var in self.filter_vars.items() if var.get()]
                return gallery_download(
                    url=url,
                    output_dir=output_dir,
                    filename=filename,
                    selected_exts=selected_exts,
                    log_func=self.log,
                    status_func=self.status_var.set,
                    cancel_check_func=lambda: self._cancel_requested,
                    proc_register=self.processes.append
                )
        finally:
            self.enable_ui()