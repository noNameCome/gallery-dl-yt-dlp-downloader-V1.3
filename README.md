# gallery-dl-yt-dlp-downloader-V1.4
gallery-dl,yt-dlp-downloader V1.4(KOREAN)

![Image](https://github.com/user-attachments/assets/c9900799-0314-4567-9d24-0ed8bc6aa0f4)

---

### 📥 요구사항

## Installation
Python 3.4+,ffmpeg
```bash
https://www.python.org/downloads/
```
```bash
https://ffmpeg.org/download.html
```

### Pip
```bash
pip install gallery-dl
pip install yt-dl 
```
---

### 🔧 변경사항
※ gallery-dl,yt-dlp 통합<br>
※ 유튜브 게시물 전체 이미지 크롤링 기능 추가 <br>
※ 각종 오류 수정<br>
※ config.json 샘플 파일 수정 <br>
※ 에러시 재시도 제거 <br>

---
### ⚙️ ffmpeg 설정법
```bash
https://ffmpeg.org/download.html
```
📁 ffmpeg.exe , ffprobe.exe -> [root 폴더에 있는 ffmpeg 내부 설치] 

---

### ⚙️ config.json 설정법
`config.json`에 있는 내용을 전체 선택 후  
`C:\\Users\\계정폴더\\gallery-dl\\config.json` 에 덮어쓰기 하면 됩니다.  
(※ `config 열기` 버튼 클릭 후 거기에 넣으면 됨)  
*안해도 됨, 그냥 사용해도 됨*

`config`은 본인이 스스로 알아서 수정하는 방법 밖에 없음...  
gallery-dl --list-keywords (url) > cmd 명령어 실행

```bash
gallery-dl --list-keywords (url)
```
