# youtube-downloader
An simple Youtube video downloader in python.
Supported formats are: mp4, m4a, webm
Resoulion supported: up to 2160p

Known issue:
1 - After canceling any download, the program maintein the file unfinished.

### How to build by yourself:

Step one - Activate the venv.
```bash
VirutalAmbient\Scripts\activate.bat
```
Step two - Use the pyinstaller
```bash
pyinstaller --noconsole --onefile youtube-downloader.py
```
