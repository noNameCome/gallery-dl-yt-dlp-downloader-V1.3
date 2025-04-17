import subprocess
import os
import re
import signal
import time
from urllib.parse import urlparse
import psutil

CREATE_NO_WINDOW = 0x08000000

def is_youtube(url):
    netloc = urlparse(url).netloc
    return "youtube.com" in netloc or "youtu.be" in netloc

def kill_proc_tree(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except Exception as e:
        print(f"❌ 프로세스 종료 실패: {e}")

def run_ytdlp(url, output_path, filename, log_func, resolution="720", audio_only=False, cancel_check_func=lambda: False):
    log_func(f"▶ yt-dlp 실행: {url}")
    try:
        ffmpeg_path = os.path.abspath(os.path.join("ffmpeg", "ffmpeg.exe"))
        youtube_output_path = os.path.join(output_path, "youtube")
        os.makedirs(youtube_output_path, exist_ok=True)

        if filename:
            filename = re.sub(r'[\\/:*?\"<>|]', '', filename)
            output_template = f"{filename}.%(ext)s"
            filename_base = filename
        else:
            output_template = "%(title)s.%(ext)s"
            filename_base = None

        command = ["yt-dlp", url, "-P", youtube_output_path, "--no-playlist", "--no-part", "-o", output_template]

        if audio_only:
            command += [
                "-x", "--audio-format", "mp3",
                "--audio-quality", "320k",
                "--ffmpeg-location", ffmpeg_path
            ]
        else:
            command += [
                "-f", f"bestvideo[height<={resolution}]+bestaudio/best",
                "--remux-video", "mp4",
                "--ffmpeg-location", ffmpeg_path
            ]

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=CREATE_NO_WINDOW | (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
        )

        while proc.poll() is None:
            if cancel_check_func():
                log_func("⛔ 취소 감지 → yt-dlp 중단 및 임시 파일 삭제")
                kill_proc_tree(proc.pid)
                if filename_base:
                    cleanup_ytdlp_files(youtube_output_path, filename_base, log_func)
                else:
                    cleanup_ytdlp_temp_files(youtube_output_path, log_func)
                return False

            line = proc.stdout.readline()
            if line:
                log_func(line.strip())

        return proc.returncode == 0

    except Exception as e:
        log_func(f"❌ yt-dlp 오류: {e}")
        return False

def smart_download(url, output_dir, filename, log_func, resolution="720", audio_only=False, cancel_check_func=lambda: False):
    try:
        import yt_dlp
    except ImportError:
        log_func("❌ yt-dlp 모듈이 설치되지 않았습니다.")
        return False

    if is_youtube(url):
        return run_ytdlp(
            url=url,
            output_path=output_dir,
            filename=filename,
            log_func=log_func,
            resolution=resolution,
            audio_only=audio_only,
            cancel_check_func=cancel_check_func
        )
    return None

def cleanup_ytdlp_temp_files(download_dir, log_func, window_seconds=300):
    try:
        now = time.time()
        exts = [".webm", ".mp4", ".mkv", ".m4a", ".part", ".temp"]
        deleted = 0

        for file in os.listdir(download_dir):
            path = os.path.join(download_dir, file)
            if not os.path.isfile(path):
                continue

            is_target_ext = any(file.endswith(ext) for ext in exts)
            is_temp_name = re.search(r"\.f\d{3,4}\.", file)
            is_recent = now - os.path.getmtime(path) < window_seconds

            if is_target_ext and (is_recent or is_temp_name):
                os.remove(path)
                log_func(f"🧹 yt-dlp 임시/중간 파일 삭제됨: {path}")
                deleted += 1

        if deleted == 0:
            log_func("ℹ️ 삭제된 yt-dlp 임시 파일 없음")
    except Exception as e:
        log_func(f"⚠️ yt-dlp 파일 삭제 실패: {e}")

def download_gallery(url, output_dir, filename, selected_exts, log_func, status_func, cancel_check_func, proc_register):
    try:
        command = ["gallery-dl", "-d", output_dir]
        if selected_exts:
            ext_list_str = ", ".join(f"'{ext}'" for ext in selected_exts)
            command += ["--filter", f"extension in ({ext_list_str})"]

        if filename:
            command += ["-o", f"filename={filename}_{{num}}.{{extension}}"]

        command.append(url)
        log_func(f"명령어 실행: {' '.join(command)}")

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=CREATE_NO_WINDOW | (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
        )
        proc_register(proc)

        downloaded = 0
        total_guess = 30

        while proc.poll() is None:
            if cancel_check_func():
                log_func("⛔ 취소 감지됨 → 프로세스 트리 강제 종료")
                kill_proc_tree(proc.pid)
                return False

            line = proc.stdout.readline()
            if line:
                line = line.strip()
                log_func(line)
                if "[download]" in line:
                    downloaded += 1
                    percent = min(int((downloaded / total_guess) * 100), 100)
                    status_func(f"상태: 다운로드 중... {percent}%")

        if proc.returncode == 0:
            status_func("상태: 완료")
            log_func("✅ 다운로드 완료")
            return True
        else:
            status_func("상태: 오류")
            log_func(f"❌ gallery-dl 에러 코드: {proc.returncode}")
            return False

    except Exception as e:
        log_func(f"❌ gallery-dl 오류 발생: {e}")
        status_func("상태: 실패")
        return False
