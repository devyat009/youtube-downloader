# youtube-downloader
A simple YouTube video downloader in Python, HTML, CSS and JavaScript using the [yt-dlp](https://github.com/yt-dlp/yt-dlp) under the hood.



- Supported formats: mp4
- Resolution supported: up to 2160p 60fps
- Auto audio quality selection.

The interface:

![youtube-downloader-screenshot1](https://github.com/user-attachments/assets/00882e6f-e3d6-49ce-84ab-4db77d710f71)

When downloading:

![youtube-downloader-screenshot2](https://github.com/user-attachments/assets/0e90b7e6-1142-42da-a33f-e0a8019702d0)


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
