import subprocess
import os
import re
import signal
import time
from urllib.parse import urlparse
import psutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
from urllib.parse import parse_qs, unquote
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

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

def get_channel_name_from_url(url):
    try:
        import yt_dlp
        info = yt_dlp.YoutubeDL().extract_info(url, download=False)
        return info.get("channel").replace("/", "_")
    except:
        return "unknown_channel"

def run_ytdlp(url, output_path, filename, log_func, resolution="720", audio_only=False, cancel_check_func=lambda: False):
    log_func(f"▶ yt-dlp 실행: {url}")
    try:
        ffmpeg_path = os.path.abspath(os.path.join("ffmpeg", "ffmpeg.exe"))
        channel_name = get_channel_name_from_url(url)
        channel_name = re.sub(r'[\\\\/:*?\"<>|]', '', channel_name)  # sanitize
        youtube_output_path = os.path.join(output_path, "youtube", channel_name)

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
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            creationflags=CREATE_NO_WINDOW | (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
            env=env
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

def scroll_to_bottom(driver, log_func, pause_time=2, max_tries=20):
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    tries = 0
    while tries < max_tries:
        log_func(f"🔄 페이지 스크롤 중... (시도 {tries + 1}/{max_tries})")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            tries += 1
        else:
            tries = 0
            last_height = new_height
    log_func("✅ 스크롤 완료, 모든 게시글 로딩 완료")

def extract_channel_id(url):
    """URL에서 채널 ID를 추출"""
    try:
        from urllib.parse import unquote
        # URL 디코딩
        decoded_url = unquote(url)
        
        if '@' in decoded_url:
            # @username 형식의 URL
            channel_id = decoded_url.split('/community')[0].split('@')[-1]
        else:
            # 채널 ID 형식의 URL
            channel_id = decoded_url.split('/channel/')[-1].split('/')[0]
        
        return channel_id
    except:
        return None

def get_community_posts(channel_id, log_func=print):
    """채널의 커뮤니티 게시물을 가져옴"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
        'Origin': 'https://www.youtube.com',
        'Referer': 'https://www.youtube.com/'
    }

    try:
        # 채널 페이지 URL 생성 (인코딩된 상태 유지)
        url = f'https://www.youtube.com/@{channel_id}/community'
        
        # 첫 번째 시도
        response = requests.get(url, headers=headers)
        
        # 404 에러시 다시 시도
        if response.status_code == 404:
            # URL 인코딩하여 다시 시도
            from urllib.parse import quote
            encoded_channel_id = quote(channel_id)
            url = f'https://www.youtube.com/@{encoded_channel_id}/community'
            response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            log_func(f"❌ 채널 페이지 접근 실패: HTTP {response.status_code}")
            return None

        # ytInitialData를 추출
        html = response.text
        data_match = re.search(r'var ytInitialData = ({.*?});', html)
        if not data_match:
            # 다른 패턴으로 시도
            data_match = re.search(r'ytInitialData\s*=\s*({.*?});', html)
            if not data_match:
                log_func("❌ 채널 데이터를 찾을 수 없습니다.")
                return None

        data = json.loads(data_match.group(1))
        
        # 채널 이름 추출 (여러 경로 시도)
        try:
            if 'header' in data and 'c4TabbedHeaderRenderer' in data['header']:
                channel_name = data['header']['c4TabbedHeaderRenderer']['title']
            elif 'metadata' in data and 'channelMetadataRenderer' in data['metadata']:
                channel_name = data['metadata']['channelMetadataRenderer']['title']
            else:
                channel_name = channel_id
        except:
            channel_name = channel_id
            
        # 커뮤니티 탭의 게시물 추출 (여러 경로 시도)
        try:
            items = data['contents']['twoColumnBrowseResultsRenderer']['tabs']
            community_tab = next(tab for tab in items if tab.get('tabRenderer', {}).get('title') == 'Community')
            posts = community_tab['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        except:
            try:
                # 대체 경로 시도
                posts = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][1]['tabRenderer']['content']['sectionListRenderer']['contents']
            except:
                log_func("❌ 커뮤니티 게시물을 찾을 수 없습니다.")
                return None

        return channel_name, posts
    except Exception as e:
        log_func(f"❌ 오류 발생: {str(e)}")
        return None

def crawl_community_images_with_id(url, output_dir, log_func=print, cancel_check=lambda: False):
    log_func("🔍 유튜브 커뮤니티 이미지 크롤링 시작...")

    try:
        # URL 디코딩 (더 일찍 수행)
        decoded_url = unquote(url)
        if decoded_url != url:
            log_func(f"🔗 URL 디코딩: {url}")
            log_func(f"🔗 디코딩된 URL: {decoded_url}")

        # Chrome 옵션 설정
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # 크롬 드라이버 자동 설치 및 실행
        log_func("🔄 크롬 드라이버 준비 중...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })

        log_func("🌐 페이지 열기 중...")
        driver.get(decoded_url)
        time.sleep(2)

        # 페이지 로딩 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "ytd-backstage-post-renderer"))
            )
        except:
            log_func("⚠️ 페이지 로딩 대기 시간 초과, 계속 진행...")

        log_func("📜 전체 페이지 로딩 및 스크롤 시작")
        scroll_to_bottom(driver, log_func)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # URL에서 채널명 추출 시도
        channel_name = None
        if '@' in decoded_url:
            channel_name = decoded_url.split('@')[1].split('/')[0]
            log_func(f"📺 채널명 추출: {channel_name}")
        else:
            # 채널명 추출 시도 (여러 선택자 시도)
            channel_name_elem = soup.select_one("ytd-channel-name yt-formatted-string#text")
            if not channel_name_elem:
                channel_name_elem = soup.select_one("ytd-channel-name yt-formatted-string")
            if not channel_name_elem:
                channel_name_elem = soup.select_one("yt-formatted-string.ytd-channel-name")
            
            if channel_name_elem:
                channel_name = channel_name_elem.get_text(strip=True)
                log_func(f"📺 채널명 추출: {channel_name}")
        
        if not channel_name:
            channel_name = "unknown_channel"
            log_func("⚠️ 채널명을 찾을 수 없어 'unknown_channel'로 설정")
            
        # 채널명 정리
        original_channel_name = channel_name
        channel_name = channel_name.replace("/", "_")
        channel_name = re.sub(r'[\\/:*?"<>|]', '_', channel_name)  # 파일명으로 사용할 수 없는 문자 제거
        
        if original_channel_name != channel_name:
            log_func(f"📝 채널명 정리: {original_channel_name} → {channel_name}")
        
        # 저장 경로 설정: youtube/채널명
        youtube_dir = os.path.join(output_dir, "youtube")
        os.makedirs(youtube_dir, exist_ok=True)
        channel_dir = os.path.join(youtube_dir, channel_name)
        os.makedirs(channel_dir, exist_ok=True)
        log_func(f"📁 저장 경로 생성: {channel_dir}")

        driver.quit()

        # 모든 게시글을 역순으로 처리하기 위해 리스트로 변환
        posts = list(reversed(soup.select("ytd-backstage-post-renderer")))
        log_func(f"📦 총 게시글 수: {len(posts)}")
        success = 0
        fail = 0
        image_counter = 1

        for post in posts:
            if cancel_check():
                log_func("⛔ 작업 취소 요청됨 → 크롤링 중단")
                break

            imgs = post.find_all("img")
            for img in imgs:
                src = img.get("src")
                if not src:
                    continue
                
                log_func(f"[DEBUG] 이미지 src: {src}")

                if "yt3.ggpht.com" in src or "ytimg.com" in src:
                    # 고해상도 URL로 변환
                    highres_src = src.split('=')[0] + "=s2048"
                    filename = f"{image_counter}.jpg"
                    filepath = os.path.join(channel_dir, filename)
                    
                    # 이미 존재하는 파일 건너뛰기
                    if os.path.exists(filepath):
                        log_func(f"⚠️ Skip: {filename} (이미 존재함)")
                        continue

                    try:
                        r = requests.get(highres_src, timeout=10)
                        if r.status_code == 200:
                            with open(filepath, "wb") as f:
                                f.write(r.content)
                            log_func(f"✅ Saved: {filename}")
                            success += 1
                            image_counter += 1
                        else:
                            log_func(f"❌ Skipped: HTTP {r.status_code} → {filename}")
                            fail += 1
                    except Exception as e:
                        log_func(f"❌ Failed: {e}")
                        fail += 1

        log_func(f"\n🎯 최종 결과: 성공 {success}개, 실패 {fail}개")
        return channel_dir if success > 0 else None

    except Exception as e:
        log_func(f"❌ 크롤링 중 오류 발생: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None

def smart_download(url, output_dir, filename, log_func, resolution="720", audio_only=False, cancel_check_func=lambda: False):
    try:
        import yt_dlp
    except ImportError:
        log_func("❌ yt-dlp 모듈이 설치되지 않았습니다.")
        return False

    if "/community" in url:
        # 커뮤니티 이미지 다운로드 시도
        result = crawl_community_images_with_id(
            url, output_dir, log_func=log_func, cancel_check=cancel_check_func
        )
        # result가 None이 아니면 성공적으로 채널 디렉토리가 생성된 것
        return result is not None and not cancel_check_func()

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

            if len(selected_exts) == 1 and 'zip' in selected_exts:
                if filename:
                    command += ["-o", f"filename={filename}_{{filename}}.{{extension}}"]
            else:
                if filename:
                    command += ["-o", f"filename={filename}_{{num}}.{{extension}}"]

        command.append(url)
        log_func(f"명령어 실행: {' '.join(command)}")

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            creationflags=CREATE_NO_WINDOW | (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
            env=env
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