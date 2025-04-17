import subprocess
import os
import re
from urllib.parse import urlparse

CREATE_NO_WINDOW = 0x08000000

def is_youtube(url):
    netloc = urlparse(url).netloc
    return "youtube.com" in netloc or "youtu.be" in netloc

def run_ytdlp(url, output_path, filename, log_func, resolution="720", audio_only=False):
    log_func(f"▶ yt-dlp 실행: {url}")
    try:
        ffmpeg_path = os.path.abspath(os.path.join("ffmpeg", "ffmpeg.exe"))
        youtube_output_path = os.path.join(output_path, "youtube")
        os.makedirs(youtube_output_path, exist_ok=True)

        if filename:
            filename = re.sub(r'[\\/:*?"<>|]', '', filename)
            output_template = f"{filename}.%(ext)s"
        else:
            output_template = "%(title)s.%(ext)s"

        command = ["yt-dlp", url, "-P", youtube_output_path, "--no-playlist", "-o", output_template]

        if audio_only:
            command += ["-x", "--audio-format", "mp3", "--audio-quality", "320k", "--ffmpeg-location", ffmpeg_path]
        else:
            if resolution not in ["720", "1080", "1440", "2160"]:
                log_func("⚠ 다운로드 취소: 해상도 미선택")
                return False
            command += ["-f", f"bestvideo[height<={resolution}]+bestaudio/best", "--remux-video", "mp4", "--ffmpeg-location", ffmpeg_path]

        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                creationflags=CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)

        while proc.poll() is None:
            line = proc.stdout.readline()
            if line:
                log_func(line.strip())

        return proc.returncode == 0

    except Exception as e:
        log_func(f"오류: yt-dlp 실패: {e}")
        return False

def smart_download(url, output_dir, filename, log_func, resolution="720", audio_only=False):
    try:
        import yt_dlp
    except ImportError:
        log_func("❌ yt-dlp가 설치되지 않았습니다. 설치 후 다시 시도해주세요.")
        return False

    if is_youtube(url):
        return run_ytdlp(url, output_dir, filename, log_func, resolution, audio_only)
    return None  # gallery-dl 케이스는 UI에서 처리

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

        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                creationflags=CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
        proc_register(proc)

        downloaded = 0
        total_guess = 30

        while proc.poll() is None:
            if cancel_check_func():
                log_func("⛔ 작업 취소 감지 → subprocess 종료")
                proc.terminate()
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
            log_func("다운로드 완료!")
            return True
        else:
            status_func("상태: 오류")
            log_func(f"에러 코드: {proc.returncode}")
            return False

    except Exception as e:
        log_func(f"오류 발생: {e}")
        status_func("상태: 실패")
        return False
