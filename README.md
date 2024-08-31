# youtube-downloader
A simple YouTube video downloader in Python, HTML, CSS and JavaScript using the [yt-dlp](https://github.com/yt-dlp/yt-dlp) under the hood.

Features:
- Supported formats: mp4
- Resolution supported: up to 2160p 60fps
- Thumbnail Download.
- Auto audio quality selection.

Selecting quality:

![select](https://github.com/user-attachments/assets/56505eb6-bda1-4159-a0b8-80da2a928d35)

Download Finished:

![download finish](https://github.com/user-attachments/assets/d13e2263-9acd-4c24-ad41-394a88846cf0)


### How to build by yourself:
Step 0 - Create a Virtual Environment (Optional)
```bash
python -m venv VirtualAmbient
```
Enable it:
```bash
.\VirtualAmbient\Scripts\activate.bat
```
Step 1 - Install the dependencies.
```bash
pip install -r requirements.txt
```
Step 2 - Enter in the app folder.
```bash
cd app
```
Step 3 - Use the pyinstaller to build.
```bash
pyinstaller youtube_downloader.spec
```
