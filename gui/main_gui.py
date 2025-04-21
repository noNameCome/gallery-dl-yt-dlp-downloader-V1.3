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
import time
import collections
from PIL import Image
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
if sys.platform == "win32":
    os.system("chcp 65001")


from logic.config import load_stored_output_dir, store_output_dir
from logic.downloader import smart_download as ytdlp_smart_download
from logic.downloader import is_youtube
from logic.downloader import download_gallery as gallery_download
from logic.downloader import kill_proc_tree

CREATE_NO_WINDOW = 0x08000000
# 색상 정의
HACKER_GREEN = "#1fff1f"  # 기본 네온 그린 색상
HACKER_BG = "#0f0f0f"    # 기본 배경 색상
HACKER_DARK = "#1a1a1a"  # 어두운 배경 색상
HACKER_ACCENT = "#4dff4d" # 강조 색상
HACKER_RED = "#ff3333"    # 경고 및 취소 색상
HACKER_BLUE = "#33ffff"   # 정보 표시 색상
HACKER_YELLOW = "#ffff33" # 주의 색상
HACKER_PURPLE = "#ff33ff" # 특수 기능 색상
HACKER_ORANGE = "#ff9933" # 보조 강조 색상
HACKER_BORDER = "#2a2a2a" # 테두리 색상
TITLE_BAR_BG = "#1a1a1a"  # 타이틀바 배경 색상
TITLE_BAR_FG = "#999999"  # 타이틀바 텍스트 색상
TITLE_BAR_BUTTON_BG = "#333333"  # 타이틀바 버튼 배경 색상
TITLE_BAR_BUTTON_HOVER = "#4d4d4d"  # 타이틀바 버튼 호버 색상
TITLE_BAR_HEIGHT = 30  # 타이틀바 높이
placeholder_text = "파일이름 입력 (선택)"
DOWNLOAD_BTN_COLOR = "#ff1a1a"  # 다운로드 버튼 색상
DOWNLOAD_BTN_HOVER = "#ff4d4d"  # 다운로드 버튼 호버 색상

class GalleryDLGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("💀 GALLERY-DL DOWNLOADER")
        self.root.geometry("800x800")
        self.root.configure(bg=HACKER_BG)
        self.root.resizable(True, True)
        
        # 작업 표시줄 아이콘 설정
        try:
            if hasattr(sys, '_MEIPASS'):  # PyInstaller 환경 확인
                icon_path = os.path.join(sys._MEIPASS, "icon.ico")
            else:
                icon_path = "icon.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # 초기화
        self.processes = []
        self.stored_dir = load_stored_output_dir()
        
        # 메인 컨테이너 생성
        self.container = tk.Frame(self.root, bg=HACKER_BG)
        self.container.pack(fill="both", expand=True)
        
        # 메인 컨텐츠 프레임 생성
        self.main_frame = tk.Frame(self.container, bg=HACKER_BG)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.init_ui()
        
        # 최소 창 크기 설정
        self.root.minsize(700, 700)
        
        # 창 테두리 설정
        self.container.configure(highlightbackground=HACKER_BORDER, highlightthickness=1)
        
        # 윈도우 종료 시 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Alt+F4 키 바인딩 추가
        self.root.bind('<Alt-F4>', lambda e: self.on_closing())
        
        # 윈도우를 화면 중앙에 위치
        self.center_window()

    def center_window(self):
        """윈도우를 화면 중앙에 위치시킴"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def on_closing(self):
        """프로그램 종료 처리"""
        try:
            # 실행 중인 모든 프로세스 종료
            for proc in self.processes:
                try:
                    if os.name == "nt":
                        kill_proc_tree(proc.pid)
                    else:
                        proc.terminate()
                except:
                    pass
            
            # 윈도우 종료
            if self.root:
                self.root.quit()
                self.root.destroy()
            
            # 프로세스 완전 종료
            if hasattr(sys, 'exit'):
                sys.exit(0)
            else:
                os._exit(0)
        except:
            # 강제 종료
            os._exit(1)

    def init_ui(self):
        self.url_var = tk.StringVar()
        font = ("Malgun Gothic", 12)  # 기본 폰트
        title_font = ("Malgun Gothic", 16, "bold")  # 제목 폰트
        button_font = ("Malgun Gothic", 12)  # 버튼 폰트
        log_font = ("Consolas", 10)  # 로그 폰트는 Consolas 유지

        # Configure styles
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure scrollbar style
        style.configure("Custom.Vertical.TScrollbar",
            gripcount=0,
            background=HACKER_GREEN,
            troughcolor=HACKER_DARK,
            bordercolor=HACKER_BORDER,
            lightcolor=HACKER_BG,
            darkcolor=HACKER_BG,
            arrowcolor=HACKER_GREEN,
            relief="flat",
            width=10
        )
        
        # 버튼 스타일 업데이트
        style.configure("Custom.TButton",
            background=HACKER_DARK,
            foreground=HACKER_GREEN,
            borderwidth=1,
            relief="flat",
            font=button_font,
            padding=10
        )
        
        # 입력창 스타일 업데이트
        style.configure("Custom.TEntry",
            fieldbackground=HACKER_DARK,
            foreground=HACKER_GREEN,
            borderwidth=1,
            relief="flat"
        )

        # Main container with padding
        main_container = tk.Frame(self.main_frame, bg=HACKER_BG)
        main_container.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Title with ASCII art style
        title_frame = tk.Frame(main_container, bg=HACKER_BG)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="[ GALLERY-DL 다운로더 ]", font=title_font, bg=HACKER_BG, fg=HACKER_GREEN)
        title_label.pack(side="left")
        
        subtitle_label = tk.Label(title_frame, text="by noName_Come", font=("Malgun Gothic", 10), bg=HACKER_BG, fg=HACKER_ACCENT)
        subtitle_label.pack(side="left", padx=(10, 0), pady=(5, 0))
        
        # URL input section
        url_section = tk.Frame(main_container, bg=HACKER_BG)
        url_section.pack(fill="x", pady=(0, 15))
        
        url_label = tk.Label(url_section, text="[ URL 입력 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        url_label.pack(anchor="w", pady=(0, 5))
        
        self.url_container = tk.Frame(url_section, bg=HACKER_BG)
        self.url_container.pack(fill="x")
        
        self.url_sets = []
        self.add_url_field()  # 초기 한 개 필드 추가
        
        # URL control buttons
        url_controls = tk.Frame(url_section, bg=HACKER_BG)
        url_controls.pack(fill="x", pady=(10, 0))
        
        self.add_url_btn = tk.Button(url_controls, text="[ + ADD URL ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.add_url_field, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.add_url_btn.pack(side="left", padx=(0, 10))
        
        self.remove_url_btn = tk.Button(url_controls, text="[ - REMOVE URL ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.remove_url_field, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.remove_url_btn.pack(side="left", padx=(0, 10))

        self.clear_url_btn = tk.Button(url_controls, text="[ URL 초기화 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.clear_all_urls, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.clear_url_btn.pack(side="left")
        
        # Output directory section
        output_section = tk.Frame(main_container, bg=HACKER_BG)
        output_section.pack(fill="x", pady=(0, 15))
        
        output_label = tk.Label(output_section, text="[ 저장위치 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        output_label.pack(anchor="w", pady=(0, 5))
        
        output_frame = tk.Frame(output_section, bg=HACKER_BG)
        output_frame.pack(fill="x")
        
        self.output_dir_var = tk.StringVar(value=self.stored_dir or os.getcwd())
        self.output_entry = tk.Entry(output_frame, textvariable=self.output_dir_var, width=50, font=font, bg=HACKER_DARK, fg=HACKER_GREEN, insertbackground=HACKER_GREEN, relief="flat", highlightthickness=1, highlightbackground=HACKER_BORDER)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(output_frame, text="[ BROWSE ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.browse_output_dir, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        browse_btn.pack(side="left")
        
        # Action buttons
        action_frame = tk.Frame(main_container, bg=HACKER_BG)
        action_frame.pack(fill="x", pady=(0, 15))
        
        self.download_btn = tk.Button(action_frame, text="[ ⬇ DOWNLOAD ]", font=("Malgun Gothic", 12, "bold"), width=15, bg=DOWNLOAD_BTN_COLOR, fg=HACKER_BG, relief="flat", activebackground=DOWNLOAD_BTN_HOVER, activeforeground=HACKER_BG, command=self.start_download, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.download_btn.pack(side="left", padx=(0, 10))
        
        self.play_btn = tk.Button(action_frame, text="[ 📂 OPEN FOLDER ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.open_download_folder, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.play_btn.pack(side="left", padx=(0, 10))
        
        config_btn = tk.Button(action_frame, text="[ ⚙ CONFIG ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.open_or_create_config, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        config_btn.pack(side="left", padx=(0, 10))

        new_window_btn = tk.Button(action_frame, text="[ 추가 다운로더 열기 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.open_new_window, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        new_window_btn.pack(side="left")
        
        # File extension filters
        filters_section = tk.Frame(main_container, bg=HACKER_BG)
        filters_section.pack(fill="x", pady=(0, 15))
        
        filters_label = tk.Label(filters_section, text="[ 확장자 선택(미선택시 전체 다운) ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        filters_label.pack(anchor="w", pady=(0, 5))
        
        filters_frame = tk.Frame(filters_section, bg=HACKER_BG)
        filters_frame.pack(fill="x")
        
        self.filter_vars = {ext: tk.BooleanVar() for ext in ["zip", "mp4", "jpeg", "png", "gif"]}
        
        for ext, var in self.filter_vars.items():
            cb = tk.Checkbutton(filters_frame, text=f"[{ext}]", variable=var, font=font, bg=HACKER_BG, fg=HACKER_GREEN, selectcolor=HACKER_DARK, activebackground=HACKER_BG, activeforeground=HACKER_GREEN, cursor="hand2")
            cb.pack(side="left", padx=(0, 15))
        
        # YouTube options section
        youtube_section = tk.Frame(main_container, bg=HACKER_BG)
        youtube_section.pack(fill="x", pady=(0, 15))
        
        youtube_label = tk.Label(youtube_section, text="[ 유튜브 옵션 선택 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        youtube_label.pack(anchor="w", pady=(0, 5))
        
        self.youtube_frame = tk.Frame(youtube_section, bg=HACKER_BG)
        self.youtube_frame.pack(fill="x")
        
        resolution_label = tk.Label(self.youtube_frame, text="해상도:", font=font, bg=HACKER_BG, fg=HACKER_GREEN)
        resolution_label.pack(side="left", padx=(0, 10))
        
        self.resolution_var = tk.StringVar(value="720")
        for res in ["720", "1080", "1440", "2160"]:
            btn = tk.Radiobutton(self.youtube_frame, text=f"[{res}]", variable=self.resolution_var, value=res, font=font, bg=HACKER_BG, fg=HACKER_GREEN, selectcolor=HACKER_DARK, activebackground=HACKER_BG, activeforeground=HACKER_GREEN, cursor="hand2")
            btn.pack(side="left", padx=(0, 15))
        
        self.audio_only_var = tk.BooleanVar(value=False)
        audio_cb = tk.Checkbutton(self.youtube_frame, text="[ MP3 ONLY ]", variable=self.audio_only_var, font=font, bg=HACKER_BG, fg=HACKER_GREEN, selectcolor=HACKER_DARK, activebackground=HACKER_BG, activeforeground=HACKER_GREEN, cursor="hand2")
        audio_cb.pack(side="left")
        self.audio_only_var.trace_add("write", self.toggle_resolution_buttons)
        
        # Log section
        log_section = tk.Frame(main_container, bg=HACKER_BG)
        log_section.pack(fill="both", expand=True, pady=(0, 15))
        
        log_label = tk.Label(log_section, text="[ 로그 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        log_label.pack(anchor="w", pady=(0, 5))
        
        log_frame = tk.Frame(log_section, bg=HACKER_BG)
        log_frame.pack(fill="both", expand=True)
        
        self.output_log = tk.Text(log_frame, width=90, height=10, font=log_font, bg=HACKER_DARK, fg=HACKER_GREEN, insertbackground=HACKER_GREEN, relief="flat", wrap="word", highlightthickness=1, highlightbackground=HACKER_BORDER)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.output_log.yview, style="Custom.Vertical.TScrollbar")
        
        self.output_log.configure(yscrollcommand=scrollbar.set)
        self.output_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status and cancel button
        status_frame = tk.Frame(main_container, bg=HACKER_BG)
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.status_var = tk.StringVar(value="[ 상태: 대기중 ]")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, anchor='w', font=font, bg=HACKER_BG, fg=HACKER_GREEN)
        self.status_label.pack(side="left", fill='x', expand=True)
        
        self.cancel_button = tk.Button(status_frame, text="[ ⛔ CANCEL ]", font=button_font, bg=HACKER_DARK, fg=HACKER_RED, relief="flat", activebackground=HACKER_RED, activeforeground=HACKER_BG, command=self.cancel_download, state=tk.DISABLED, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER)
        self.cancel_button.pack(side="right")

    def add_url_field(self):
        row_frame = tk.Frame(self.url_container, bg=HACKER_BG)
        row_frame.pack(fill="x", pady=6)

        # 입력창 스타일 설정
        entry_style = {
            "font": ("Malgun Gothic", 12),
            "bg": HACKER_DARK,
            "fg": HACKER_GREEN,
            "insertbackground": HACKER_GREEN,
            "highlightbackground": HACKER_BORDER,
            "highlightcolor": HACKER_GREEN,
            "highlightthickness": 1,
            "insertwidth": 2,
            "relief": "flat"
        }

        # URL 입력 필드
        url_entry = tk.Entry(row_frame, **entry_style)
        url_entry.insert(0, "URL을 입력하세요")
        url_entry.pack(side="top", fill="x", padx=2, ipady=5)
        url_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(url_entry, "URL을 입력하세요"))
        url_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(url_entry, "URL을 입력하세요"))

        # 파일이름 입력 필드
        filename_entry = tk.Entry(row_frame, **entry_style)
        filename_entry.insert(0, "파일이름 입력 (선택)")
        filename_entry.pack(side="top", fill="x", padx=2, pady=(4, 0), ipady=3)
        filename_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(filename_entry, "파일이름 입력 (선택)"))
        filename_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(filename_entry, "파일이름 입력 (선택)"))

        self.url_sets.append((url_entry, filename_entry, row_frame))

        # Adjust window size
        new_height = 800 + len(self.url_sets) * 60
        self.root.geometry(f"800x{new_height}")

    def toggle_resolution_buttons(self, *args):
        state = tk.DISABLED if self.audio_only_var.get() else tk.NORMAL
        for child in self.youtube_frame.winfo_children():
            if isinstance(child, tk.Radiobutton):
                child.config(state=state)

    def remove_url_field(self):
        if len(self.url_sets) > 1:
            _, _, row_frame = self.url_sets.pop()
            row_frame.destroy()

            # Adjust window size
            new_height = 800 + len(self.url_sets) * 60
            self.root.geometry(f"800x{new_height}")

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
        # 로그 출력 함수 정의
        def log(msg):
            self.log_area.insert(tk.END, msg + "\n")
            self.log_area.see(tk.END)

        # 취소 확인 함수 정의
        def cancel():
            return self._cancel_requested

        # 다운로드 실행
        result = ytdlp_smart_download(
            url, output_dir, filename=None,
            log_func=self.thread_safe_log,
            resolution=self.resolution_var.get(),
            audio_only=self.audio_only_var.get(),
            cancel_check_func=cancel
        )

        # 다운로드 결과 처리
        if isinstance(result, str):
            self.last_community_path = result

        self.status_var.set("[ 상태: 완료 ]" if result else "[ 상태: 실패 ]")
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")

    def thread_safe_log(self, msg):
        # 스레드 안전한 로그 출력
        self.root.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg):
        # 로그 메시지 추가
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
        total_urls = len(url_info_list)

        try:
            for idx, (url, filename) in enumerate(url_info_list, start=1):
                self.status_var.set(f"[ 상태: 다운로드 중 ({idx}/{total_urls}) ]")
                success = self.smart_download(url, output_dir, idx, filename)

                if not success:
                    self.log(f"❌ 실패: {url}")
                    failed_urls.append(url)

            if failed_urls:
                self.log("🚫 다음 URL에서 실패했습니다:")
                for f in failed_urls:
                    self.log(f"    - {f}")
                self.status_var.set("[ 상태: 일부 실패 ]")
            else:
                self.status_var.set("[ 상태: 완료 ]")
                self.log("✅ 모든 다운로드가 완료되었습니다!")
        finally:
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
        self.status_var.set("[ 상태: 다운로드 중 ]")
        self.log("다운로드를 시작합니다...")

        threading.Thread(target=self.download_multiple, args=(url_info, output_dir)).start()

    def cancel_download(self):
        self._cancel_requested = True
        self.status_var.set("[ 상태: 취소 중 ]")
        self.log("⛔ 취소 요청됨 → 모든 다운로드를 중지합니다...")

        for proc in self.processes:
            try:
                if os.name == "nt":
                    self.log(f"⚠ FORCE TERMINATION ATTEMPT (PID: {proc.pid})")
                    kill_proc_tree(proc.pid)  # ✅ 여기 핵심!
                else:
                    proc.terminate()
            except Exception as e:
                self.log(f"⚠️ PROCESS TERMINATION FAILED: {e}")

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
                    self.log("⚠ 다운로드 취소: 해상도가 선택되지 않았습니다.")
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
        except Exception as e:
            self.log(f"❌ 다운로드 중 오류 발생: {str(e)}")
            return False

    def open_new_window(self):
        """새 창 열기"""
        # 새 창 생성을 위한 Toplevel 대신 새로운 프로세스 시작
        if sys.platform == "win32":
            subprocess.Popen([sys.executable, sys.argv[0]], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([sys.executable, sys.argv[0]])

    def clear_all_urls(self):
        # 모든 URL 입력 필드 초기화
        for url_entry, filename_entry, _ in self.url_sets:
            url_entry.delete(0, tk.END)
            url_entry.insert(0, "URL을 입력하세요")
            filename_entry.delete(0, tk.END)
            filename_entry.insert(0, "파일이름 입력 (선택)")

        # 첫 번째 URL 세트만 남기고 나머지 제거
        while len(self.url_sets) > 1:
            _, _, row_frame = self.url_sets.pop()
            row_frame.destroy()

        # 창 크기 조정
        new_height = 800 + len(self.url_sets) * 60
        self.root.geometry(f"800x{new_height}")