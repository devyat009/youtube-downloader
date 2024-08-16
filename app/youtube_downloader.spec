from PyInstaller.utils.hooks import collect_data_files
from pathlib import Path

# Colete os arquivos de recursos
datas = [
    ('resources/ffmpeg/ffmpeg.exe', 'resources/ffmpeg'),
    ('resources/index.html', 'resources'),
    ('resources/qwebchannel.js', 'resources'),
    ('resources/scripts.js', 'resources'),
    ('resources/styles.css', 'resources')
]

a = Analysis(
    ['youtube_downloader.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='youtube_downloader',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)
