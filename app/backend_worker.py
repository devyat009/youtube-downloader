import os
import re
import sys
import threading
import requests
from yt_dlp import YoutubeDL
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWebChannel import QWebChannel

# TESTING PURPOSES - Dumping the JSON
import json
import shutil

class vid_downloader_backend(QObject):
    '''
    Info:
    ---------
    The backend, where it process the URL, get resolutions available, download and more.
    - @Author Devyat009
    - @Version 1.2
    '''
    # Used to send the progress to the frontend.
    download_progress_signal = pyqtSignal(str, str, str, str)
    errorSignal = pyqtSignal(str) # Used to send the backend errors to the frontend or other messages.
    def __init__(self):
        super().__init__()
        self.ffmpeg_path = '.resources/ffmpeg/ffmpeg.exe'
        self.folder_path = None
        self.user_selected_resolution = None
        self.user_selected_id = None
        self.auto_audio_select_id = None
        self.url_path = None
        self.thumbnail_url = None
        self.video_id_list = []
        # Process and Download Threads.
        self.stop_download_event = threading.Event()
        self.download_thread = None
        self.process_url_thread = None
        self.total_size = None # Used to save the filesize for transmitting the size for the front end on the '_download_vid_thread' def.
        
        # Verify if is being used on a executable file.
        if hasattr(sys, '_MEIPASS'):
            self.ffmpeg_path = os.path.join(sys._MEIPASS, 'resources', 'ffmpeg', 'ffmpeg.exe')
        else:
            # Path for developing 
            self.ffmpeg_path = './app/resources/ffmpeg/ffmpeg.exe'
    
    @pyqtSlot(str)
    def sendError(self, message):
        self.errorSignal.emit(message)
    
    # User paste the url and this function process and starts the thread.
    @pyqtSlot(str, result=str)
    def process_url(self, message):
        self.url_path = message # Saves the user pasted url.
        self.process_url_thread = threading.Thread(target=self._process_url_thread())
        self.process_url_thread.start()
        return ""
    def _process_url_thread(self):
        self.video_id_list = self.get_video_formats(self.url_path)
    
    # Open the FileDialog with the PyQt and get the complete path and send it to the WebView.
    @pyqtSlot(result=str)
    def select_folder(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(None, "Select Folder", "", options=options)
        if folder:
            self.folder_path = folder
            return folder # Return the path for showing in the frontend.
    
    # Get the file option list. (WIP)
    @pyqtSlot(result=list)
    def get_file_options(self):
        try:
            if self.video_id_list:
                # MP4 Only available option until now...
                file_options = ['mp4']
                return list(file_options)
            else:
                return []
        except Exception as error:
            self.sendError(f"Something went wrong on 'get_file_options', error: {error}")   
    
    # Get the resolution list and sort to show on the frontend. (WIP)
    @pyqtSlot(result=list)
    def get_resolution_options(self):
        try:
            def resolution_key(fmt):
                resolution = fmt.get('resolution')
                if resolution is None:
                    return 0
                # Extract the numerical part of the resolution key to sort: '1080p' -> 1080; For whatever reason renaming resolution key as int doest work, but if is '1080p' it works :/
                return int(resolution.replace('p', ''))
            if self.video_id_list:
                # Filter the id's that does't has any resolution or incomplete.
                filtered_id_list = [
                    fmt for fmt in self.video_id_list
                    if fmt.get('resolution') and fmt.get('filesize')
                ]
                sorted_video_id_list = sorted(filtered_id_list, key=resolution_key)
                self.auto_audio_select_id = self.get_audio_format_id() # used just to call the self.auto_audio_select_size
                for audio_size in self.video_id_list: # Auto increment the audio size to the video size depending on quality(WIP)
                    if self.auto_audio_select_id == audio_size['format_id']:
                        self.auto_audio_select_size == audio_size['filesize']
                    else:
                        self.auto_audio_select_size = 0
                resolution_options = [f'{fmt['resolution']} - {self.format_size(fmt['filesize'] + self.auto_audio_select_size)}' for fmt in sorted_video_id_list]
                return resolution_options
            else:
                return []
        except Exception as error:
            self.sendError(f'ERROR - Exception caught on get_resolutions: {error}')
    
    def format_size(self, size):
        '''
        Info:
        ---------
        Add the proper size of the file to show.
        '''
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} {unit}"
    
    def estimate_filesize(self, duration, bitrate):
        '''
        Estimates the file size based in duration and bitrate.
        '''
        # Conversion of Kbps bitrate to bps.
        bitrate_bps = bitrate * 1000
        # Calculates the size in bytes.
        filesize_bytes = (duration * bitrate_bps) / 8
        # Return the ~ approximate size.
        return filesize_bytes
    
    def get_video_formats(self, url):
        '''
        Get the video formats and filter them to show the important ones.
        - @version 1.1
        '''
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Try acquire the best quality available.
                ydl_opts = {
                    'format': 'best',
                    'listformats': True
                }
                with YoutubeDL(ydl_opts) as ydl:
                    try:
                        information = ydl.extract_info(url, download=False)
                        formats_information = information.get('formats', [])
                        self.thumbnail_url = information.get('thumbnail')
                        self.get_thumbnail()
                        duration = information.get('duration', 0)  # Video Duration in seconds (Used to calculate vp09 videos).
                        video_id_list = [] # Main list.
                        video_60fps_list = [] # Used to separate and later merge to video_id_list.
                        video_30fps_list = [] # Used to separate and later merge to video_id_list.
                        video_audio_list = [] # Used to separate and later merge to video_id_list.
                        out_of_scope_list = [] # Used to find cases when does't enters in any of the above lists
                        if formats_information:
                            for fmt in formats_information:
                                # List items variables:
                                codec_short = fmt.get('vcodec', 'N/A')[:4]
                                fps = fmt.get('fps')
                                # Ignored items:
                                if codec_short == 'av01':
                                    continue
                                if '-drc' in fmt['format_id']:
                                        continue
                                
                                # File Size Rename:
                                filesize = fmt.get('filesize', None)
                                if filesize is not None:
                                    filesize = fmt.get('filesize')
                                else:
                                    #Estimate filesize if not provided
                                    bitrate = fmt.get('tbr', None)  # Bitrate in Kbps
                                    if bitrate is not None:
                                        estimated_filesize = self.estimate_filesize(duration, bitrate)
                                        filesize = estimated_filesize
                                    
                                # Resolution Rename
                                resolution = fmt.get('resolution')
                                resolution_map = {
                                    '7680x4320': '4320p',
                                    '3840x2160': '2160p',
                                    '2560x1440': '1440p',
                                    '1920x1080': '1080p',
                                    '1280x720': '720p',
                                    '854x480': '480p',
                                    '640x360': '360p',
                                    '426x240': '240p',
                                    '256x144': '144p',
                                }
                                resolution = resolution_map.get(resolution, resolution)
                                
                                # Audio Filter
                                audio_quality = fmt.get('abr')
                                if fmt['ext'] in ['webm', 'm4a'] and fmt.get('acodec') and audio_quality:
                                    audio_codec = fmt['acodec'][:4]
                                    if audio_codec == 'opus' or audio_codec == 'mp4a':
                                            if audio_quality < 64:
                                                audio_codec = fmt['acodec']
                                                audio_quality = 'low'
                                            elif 64 <= audio_quality < 128:
                                                audio_codec = fmt['acodec']
                                                audio_quality = 'medium'
                                            else:
                                                audio_codec = fmt['acodec']
                                                audio_quality = 'high'
                                            video_audio_list.append({
                                                'format_id': fmt['format_id'],
                                                'acodec': audio_codec,
                                                'abr': audio_quality,
                                                'filesize': filesize,
                                            })
                                    else:
                                        self.sendError('Cant append any audio to the video_audio_list')
                                
                                # Format Filter
                                if fmt['ext'] in ['mp4', 'mp3', 'mkv', 'm4a']:
                                    # Next Stage: filter for format_note
                                    if 'format_note' in fmt and fmt['format_note']:
                                        if fmt['format_note'] in ['144p', '240p', '360p', '480p', '720p', '720p60', '720p50', '1080p', '1080p60', '1080p50', '1440p', '1440p60', '1440p50', '2160p', '2160p60', '2160p50']:
                                            # Ignore any m3u8 protocols (I forgot why)
                                            if fmt['protocol'] == 'm3u8_native':
                                                continue
                                            # 60fps Filter
                                            if resolution in ['720p', '1080p'] and fps in [60,50]:
                                                video_60fps_list.append({'format_id':fmt['format_id'],
                                                                'filetype':fmt['ext'],
                                                                'resolution':resolution,
                                                                'filesize':filesize,
                                                                'codec':codec_short,
                                                                'format_note': fmt['format_note'],
                                                                'fps': fps
                                                                })
                                            # If the resolutions are lower than 720p and has 30fps will be added to the video_id_list in the end, because YouTube doesn't have 480p60fps.
                                            elif resolution in ['144p', '240p', '360p', '480p'] and fps in [30,25,24]:
                                                if fmt['acodec'] == 'none':
                                                    video_30fps_list.append({'format_id':fmt['format_id'],
                                                                            'filetype':fmt['ext'],
                                                                            'resolution':resolution,
                                                                            'filesize':filesize,
                                                                            'codec':codec_short,
                                                                            'format_note': fmt['format_note'],
                                                                            'acodec': fmt['acodec'],
                                                                            'fps': fps
                                                                            })
                                            # Special filter for 720p/1080p 30fps, due YouTube having 720p in 30fps and 60fps for the 60fps videos.
                                            elif resolution in ['720p', '1080p'] and fps in [30,25,24]:
                                                exists_720p_60fps = any(fmt_60fps['resolution'] == '720p' for fmt_60fps in video_60fps_list)
                                                if not exists_720p_60fps:
                                                    video_30fps_list.append({'format_id':fmt['format_id'],
                                                                                'filetype':fmt['ext'],
                                                                                'resolution':resolution,
                                                                                'filesize':filesize,
                                                                                'codec':codec_short,
                                                                                'format_note': fmt['format_note'],
                                                                                'acodec': fmt['acodec'],
                                                                                'fps': fps
                                                                                })
                                            # Out of scope:
                                            else:
                                                print('Something out of the scope was found, find out what is it with the out_of_scope_list.')
                                                out_of_scope_list.append({'format_id':fmt['format_id'],
                                                                            'filetype':fmt['ext'],
                                                                            'resolution':resolution,
                                                                            'filesize':filesize,
                                                                            'codec':codec_short,
                                                                            'acodec': fmt['acodec'],
                                                                            'fps': fps
                                                                            })
                                                #continue
                                    # Next Stage: filter for resolution, used for resolutions equal 1080p or higher due use of vp09 codec.
                                    elif 'resolution' in fmt and fmt['resolution'] in ['2560x1440', '3840x2160', '7680x4320']:
                                        #if fmt['protocol'] == 'https': # add a proper filter for hdr videos
                                        #    continue
                                        #FPS Filter
                                        if resolution in ['1440p', '2160p', '4230p'] and fps in [60,50]:
                                            video_60fps_list.append({'format_id':fmt['format_id'],
                                                                'filetype':fmt['ext'],
                                                                'resolution':resolution,
                                                                'filesize':filesize,
                                                                'codec':codec_short,
                                                                'fps': fps
                                                                })
                                        # If all videos are 30fps or 24fps will be added to the 30fps list.
                                        elif resolution in ['1440p', '2160p', '4320p'] and fps in [30,25,24]:
                                            video_30fps_list.append({'format_id':fmt['format_id'],
                                                                'filetype':fmt['ext'],
                                                                'resolution':resolution,
                                                                'filesize':filesize,
                                                                'codec':codec_short,
                                                                'fps': fps
                                                                })
                                        # Out of scope:
                                        else:
                                            print('Something out of the scope was found, find out what is it with the out_of_scope_list.')
                                            out_of_scope_list.append({'format_id':fmt['format_id'],
                                                                            'filetype':fmt['ext'],
                                                                            'resolution':fmt['resolution'],
                                                                            'filesize':filesize,
                                                                            'codec':codec_short,
                                                                            'acodec': fmt['acodec'],
                                                                            'fps': fps
                                                                            })
                                # Merging to the video_id_list:
                                if video_60fps_list:
                                    filtered_video_30fps_list = [i for i in video_30fps_list if not (i['resolution'] == '720p' and i['fps'] in [30, 24, 25])] # Get rid of the duplicated 720p 30fps once for all.
                                    video_id_list = filtered_video_30fps_list + video_60fps_list + video_audio_list
                                else:
                                    video_id_list = video_30fps_list + video_audio_list
                            # Return the id list, if need any list print do before return here to see what is happening on the lists:
                            # Testing purposes
                            # json_output = 'resources/d/'
                            # json_video = f'json_plane_video.json'
                            # with open(json_video, 'w') as new_file:
                            #     json.dump(formats_information, new_file, indent=4)
                            #     print('file created')
                            # shutil.move(json_video, json_output)
                            return video_id_list
                        else:
                            self.sendError('No available formats')
                    except Exception as error:
                        self.sendError(f'ERROR - Exception caught: {error}')
            else:
                #print('PLACEHOLDER - Else if not 200')
                self.sendError(f'Connection error - {response.status_code()}')
        # Connection error treatment:
        except requests.exceptions.ConnectionError:
            #print('PLACEHOLDER - Connection error')
            self.sendError('Connection error, check your internet connection!')
        except requests.exceptions.Timeout:
            #print('PLACEHOLDER - Connection was timed out')
            self.sendError('Connection was timed out, try again later')
        # Else
        except requests.exceptions.RequestException as error:
            #print(f'PLACEHOLDER - Some error occurred: {error}')
            self.sendError(f'Some error occurred on request: {error}')
    
    def get_audio_format_id(self):
        '''
        This code is responsible selecting the appropriate audio quality based on the user-selected
        video resolution. It checks the user-selected resolution and then iterates through a list of
        available audio options for the video. Depending on the resolution, it sets the
        `auto_audio_select_id` to the format ID of the audio with the corresponding quality level
        (low, medium, or high) based on the bitrate information provided in the `video_id_list`.
        '''
        self.auto_audio_select_size = 0
        # Low quality audio for low quality videos:
        if self.user_selected_resolution in ['144p', '240p', '360p']:
            for audio in self.video_id_list:
                bitrate = audio.get('abr')
                if bitrate == 'low':
                    self.auto_audio_select_id = audio['format_id']
                    self.auto_audio_select_size = audio.get('filesize', 0)
                    break
        # Medium quality audio for medium quality videos:
        elif self.user_selected_resolution in ['480p', '720p']:
            for audio in self.video_id_list:
                bitrate = audio.get('abr')
                if bitrate == 'medium':
                    self.auto_audio_select_id = audio['format_id']
                    self.auto_audio_select_size = audio.get('filesize', 0)
                    break
        # High quality audio for high quality videos:
        elif self.user_selected_resolution in ['1080p', '1440p', '2160p']:
            for audio in self.video_id_list:
                bitrate = audio.get('abr')
                if bitrate == 'high':
                    self.auto_audio_select_id = audio['format_id']
                    self.auto_audio_select_size = audio.get('filesize', 0)
                    break
        return self.auto_audio_select_id
    
    # Get the user selected resolution (WIP)
    @pyqtSlot(str)
    def set_selected_resolution(self, resolution):
        self.user_selected_resolution = resolution
        string_part = self.user_selected_resolution.split(' - ')
        self.user_selected_resolution = string_part[0]
        for i in self.video_id_list:
            if self.user_selected_resolution == i['resolution']:
                self.user_selected_id = i['format_id']
                # AUTO AUDIO QUALITY SELECT 
                self.auto_audio_select_id = self.get_audio_format_id()
                return self.user_selected_id, self.auto_audio_select_id # Double check if will add the format id to the variable.
    
    # Get the video thumbnail
    @pyqtSlot(result=str)
    def get_thumbnail(self):
        image = f'{self.thumbnail_url}'
        return image

    # DOWNLOAD BUTTON WIP
    @pyqtSlot(result=str)
    def download_vid(self):
        self.stop_download_event.clear()  # Clear the thread event
        self.download_thread = threading.Thread(target=self._download_vid_thread)
        self.download_thread.start()
        return "Download initiated"
        
    def _download_vid_thread(self):
        ydl_opts = {
            'merge_output_format': 'mp4',
            'format': f'{self.user_selected_id} + {self.auto_audio_select_id}',
            'outtmpl': f'{self.folder_path}/%(title)s_{self.user_selected_resolution}_{self.user_selected_id}.%(ext)s',
            'ffmpeg_location': self.ffmpeg_path,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Convert to mp4 after download
            }],
            'noprogress': True,
            'overwrites': True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                self.last_filename = None  # Track the last filename to detect changes.
                def download_hook(d):
                    if self.stop_download_event.is_set():
                        raise Exception("Download canceled by user.")
                    
                    if d['status'] == 'downloading':
                    # Detect filename change to identify if it's a new file.
                        if self.last_filename != d['filename']:
                            self.last_filename = d['filename']

                            # Check if the file is the audio file based on format ID.
                            if self.auto_audio_select_id in d['filename'] or d['filename'].endswith('.m4a'):
                                for user_video_format_id in self.video_id_list:
                                    if user_video_format_id['format_id'] == self.auto_audio_select_id:
                                        self.total_size = user_video_format_id.get('filesize')
                                        break

                            # Check if the file is the video file based on format ID.
                            elif self.user_selected_id in d['filename'] or d['filename'].endswith('.mp4'):
                                for user_video_format_id in self.video_id_list:
                                    if user_video_format_id['format_id'] == self.user_selected_id:
                                        self.total_size = user_video_format_id.get('filesize')
                                        break
                        # All of that just to send the correct filesize after the download changes from video to audio for the frontend :/
                        self.download_progress_str(d['_percent_str'], self.total_size, d['_eta_str'], d['_speed_str'])
                    elif 'deleting original file' in d.get('info_dict', {}).get('msg', ''):
                        print('Files are being deleted')
                        self.sendError('Video and audio files merged sucessfully')
                    elif d['status'] == 'error':
                        self.sendError(f'Error trying download the {d['filename']}')
                ydl.add_progress_hook(download_hook)
                ydl.download([self.url_path])
                self.sendError('Video and audio files merged sucessfully')
        except Exception as e:
            if str(e) == 'Download canceled by user.':
                pass # ignore this specific caught
            else:
                self.sendError(f'ERROR - Exception caught on _download_vid_thread: {e}')
            
    def download_progress_str(self, percent, total_size, time, speed):
        '''
        Function responsible to format and send to the frontend the values as strings
        '''
        # Percent Format
        percent = re.sub(r'\x1b\[[0-9;]*m', '', percent).replace('%', '').strip()
        percent = float(percent.replace('%', ''))
        percent = round(percent)
        percent = str(percent)
        # Size Format
        total_size = str(self.format_size(total_size))
        # Time format - Straight up magic here
        time_clean = re.sub(r'\x1b\[[0-9;]*m', '', time).strip()
        time_match = re.search(r'\d{2}:\d{2}', time_clean)
        time = time_match.group() if time_match else ''  # Ensure time is a string
        # Speed format - Straight up magic here
        speed_clean = re.sub(r'\x1b\[[0-9;]*m', '', speed).strip()
        speed_match = re.search(r'\d+(\.\d+)?[A-Za-z]+/s', speed_clean)
        speed = speed_match.group() if speed_match else ''  # Ensure speed is a string)
        # Send to the front end the download progress
        self.download_progress_signal.emit(percent, total_size, time, speed)
    
    @pyqtSlot()
    def cancel_download(self):
        if self.download_thread and self.download_thread.is_alive():
            self.stop_download_event.set()  # Enable the stop event 
            print("Canceling download...")
            # for when download thread end (WIP)
            self.download_thread.join()
        else:
            print("No active download to cancel.")
    # Close the app and cancel the download.
    def close_app(self):
        self.cancel_download()