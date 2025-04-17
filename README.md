# gallery-dl-yt-dlp-downloader-V1.3
gallery-dl,yt-dlp-downloader V1.3(KOREAN)

![Image](https://github.com/user-attachments/assets/6dd121af-1a3d-4dfa-b120-b2449e8ef236)

---

### 📥 요구사항

## Installation
Python 3.4+  , ffmpeg
```bash
https://www.python.org/downloads/
```

### Pip
```bash
pip install gallery-dl
pip install yt-dl 
```
---

### 🔧 변경사항
※ gallery-dl,yt-dlp 통합
※ 각종 오류 수정
※ config.json 샘플 파일 수정  
※ 에러시 재시도 제거 

---
### ⚙️ ffmpeg 설정법
```bash
https://ffmpeg.org/download.html
```
📁 ffmpeg.exe , ffprobe.exe -> [root 폴더 내부 ffmpeg 이동] 

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
