# youtube-downloader
An simple Youtube video downloader in python using the [yt-dlp](https://github.com/yt-dlp/yt-dlp) under the hood.

Note 2024/8/8 -  Coming soon new backend and interface based on html and css

- Supported formats are: mp4, m4a, webm
- Resoulion supported: up to 2160p

The interface:

![youtube-downloader-screenshot1](https://github.com/user-attachments/assets/00882e6f-e3d6-49ce-84ab-4db77d710f71)

When downloading:

![youtube-downloader-screenshot2](https://github.com/user-attachments/assets/0e90b7e6-1142-42da-a33f-e0a8019702d0)

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
