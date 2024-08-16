# youtube-downloader
A simple YouTube video downloader in Python, HTML, CSS and JavaScript using the [yt-dlp](https://github.com/yt-dlp/yt-dlp) under the hood.



- Supported formats: mp4
- Resolution supported: up to 2160p 60fps
- Auto audio quality selection.

The interface:

![youtube-downloader-screenshot1](https://github.com/user-attachments/assets/e3ec9810-cd01-4971-8f4c-fb821a833c15)


Selecting quality:

![youtube-downloader-screenshot2](https://github.com/user-attachments/assets/d753ec9c-980c-4e94-a8d5-7e52836e2a12)

When downloading:
![youtube-downloader-screenshot3](https://github.com/user-attachments/assets/00180f64-6292-4884-a855-c6487a0750a3)


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
