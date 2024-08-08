import os
import re
import threading
import tkinter as tk
import requests
from yt_dlp import YoutubeDL
from tkinter import ttk, filedialog

class YtDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Youtube Downloader')
        self.selected_resolution = None
        self.setup_ui()
        self.stop_download_event = threading.Event()
        self.stop_search_event = threading.Event()
        
    def setup_ui(self):
        '''
        Info:
        -----------
        Interface for the user
        '''
        
        '''
        Theme section
        '''
        self.style = ttk.Style()
        self.style.theme_use(themename=None)
        self.style.configure('TProgressbar', background='#04b424', troughcolor='#333333')
        
        # URL Label
        self.url_label = ttk.Label(self.root, text='Video URL:')
        self.url_label.grid(row=0, column=0, padx=10, pady=10)
        # URL Entry
        self.url_entry = ttk.Entry(self.root, width=45)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # Search button
        self.search_button = ttk.Button(self.root, text='Search', command=self.search_threading)
        self.search_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Output directory selection
        self.output_directory = ''
        self.output_label = ttk.Label(self.root, text='Output Directory:')
        self.output_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.output_entry = ttk.Entry(self.root, width=45)
        self.output_entry.grid(row=1, column=1, padx=10, pady=10)
        
        self.output_button = ttk.Button(self.root, text='Select', command=self.select_output_directory, state=tk.DISABLED)
        self.output_button.grid(row=1, column=2, padx=10, pady=10)
        
        # Format combobox
        self.format_label = ttk.Label(self.root, text='Format type:')
        self.format_label.grid(row=2, column=0, padx=10, pady=10)
        
        self.format_combobox = ttk.Combobox(self.root, width=20, state='readonly')
        self.format_combobox.grid(row=2, column=1, padx=10, pady=10)
        self.format_combobox.bind("<<ComboboxSelected>>", self.on_format_selected)
        
        # Resolution combobox
        self.resolution_label = ttk.Label(self.root, text='Resolution:')
        self.resolution_label.grid(row=3, column=0, padx=10, pady=10)
        
        self.resolution_combobox = ttk.Combobox(self.root, width=20, state='readonly')
        self.resolution_combobox.grid(row=3, column=1, padx=10, pady=10)
        self.resolution_combobox.bind("<<ComboboxSelected>>", self.on_resolution_selected)
        
        # Dowload progress bar
        self.progress_bar = ttk.Progressbar(self.root, orient='horizontal', length=200, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky= tk.W)
        
        # Cancel download
        self.cancel_button = ttk.Button(self.root, text='Cancel', command=self.cancel_download, state='disabled')
        self.cancel_button.grid(row=4, column=1, padx=0, pady=10, sticky=tk.E)
        
        # Download button
        self.download_button = ttk.Button(self.root, text='Download', command=self.download_video, state=tk.DISABLED)
        self.download_button.grid(row=4, column=2, padx=0, pady=10, sticky=tk.W)
        
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
    def search_threading(self):
        self.search_thread = threading.Thread(target=self.get_video_formats)
        self.search_thread.start()
        
    def get_video_formats(self):
        '''
        Info:
        -------
        Function to get the information of the video URL, and their formats avaible to download.
        '''
        url = self.url_entry.get()
        if not url:
            self.show_message('Insert an valid URL.')
            return
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.output_button.config(state=tk.NORMAL) # Enable output directory button
                # Define options for the best quality availble and comunicate with the progress bar.
                ydl_opts = {
                    'format': 'best',
                    'progress_hooks': [self.progress_hook],
                    'listformats': True
                }
                
                with YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        formats_info = info.get('formats', [])
                        '''
                        Extract the video informations of the URL
                        '''
                        format_and_resolution = {}
                        for item in formats_info:
                            file_extension = item['ext']
                            file_id = item['format_id']
                            resolution = item.get('resolution')
                            file_size = item.get('filesize')
                                    
                            if not file_size:
                                continue # Ignore files withou file size
                            
                            file_size_str = self.format_size(file_size)
                            
                            if file_extension not in format_and_resolution:
                                format_and_resolution[file_extension] = {
                                        'file_id': file_id,
                                        'resolutions': {} # Using a dict to map the resolutions for the file_ids
                                        }
                        
                            format_and_resolution[file_extension]['resolutions'][resolution] = {
                                'file_id': file_id,
                                'file_size': file_size_str
                            }
                        # Populate format_combobox with unique formats
                        self.format_combobox['values'] = list(format_and_resolution.keys())
                        # Store the format_and_resolution dictionary for use in on_format_selected method
                        self.format_and_resolution = format_and_resolution
                    except Exception as e:
                        self.show_message(f'Error while trying get the compatible formats: {str(e)}')
            else:
                self.show_message(f'Sorry we encountered an issue trying connect to this URL. ERROR {response.status_code}')
        
        # Some exeptions due connections errors:
        except requests.exceptions.ConnectionError:
            self.show_message('Connection error. Please check your internet connection and try again.')
        except requests.exceptions.Timeout:
            self.show_message('Request timed out. Please try again later.')
        except requests.exceptions.RequestException as e:
            self.show_message(f'An error occurred: {e}')

    def download_video(self):
        '''
        Info:
        -------
        Process to download the video.
        '''
        url = self.url_entry.get()
        if not url:
            self.show_message('Please, insert an URL.')
            return
        
        selected_format = self.selected_format
        if not selected_format:
            self.show_message('Please, select a video format.')
            return
        
        
        output_path = self.output_entry.get()
        if not output_path:
            self.show_message('Please, select the output directory')
            return
        
        # use the selcted resolution
        selected_resolution = self.selected_resolution
        if not selected_resolution:
            self.show_message('Please, select the resolution.')
            return
        
        if selected_format and selected_resolution:
            file_info = self.format_and_resolution[selected_format]['resolutions'].get(selected_resolution)
            
            if file_info:
                file_id = file_info['file_id']
                file_resolution = selected_resolution
                
                ydl_opts = {
                    'format': file_id,
                    'outtmpl': f'{output_path}/%(title)s_{file_resolution}.%(ext)s',
                    'progress_hooks': [self.progress_hook],
                }
                
                self.download_cancelled = False
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start()
                
                self.download_thread = threading.Thread(target=self.download_with_progress, args=(url, ydl_opts))
                self.download_thread.start()
                
                self.download_button.config(state='disabled')
                self.cancel_button.config(state='normal')
                
            else:
                self.show_message(f'No file ID found for resolution: {selected_resolution}')
        
    def on_format_selected(self, event):
        selected_format = self.format_combobox.get()
        if selected_format:
            resolutions = self.format_and_resolution[selected_format]['resolutions']
            # Populate resolution_combobox with resolutions for the selected format
            self.resolution_combobox['values'] = list(resolutions.keys())

    def on_resolution_selected(self, event):
        self.selected_format = self.format_combobox.get()
        self.selected_resolution = self.resolution_combobox.get()
        # Enable download button after resolution selection
        self.download_button.config(state='normal')
        
    def progress_hook(self, d):
        '''
        Info:
        ------
        The process hook.
        '''
        if d['status'] == 'downloading':
            self.root.after(0, self.update_progress, d)
        elif d['status'] == 'finished':
            self.root.after(0, self.download_complete)
        elif d['status'] == 'error':
            self.root.after(0, self.download_error)
        
    def format_eta(self, eta):
        '''
        Info:
        ------
        Format the ETA.
        '''
        return f"{eta // 60:02d}:{eta % 60:02d}"
    
    def remove_ansi_escape_sequences(self,text):
        #ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F]|[^\x20-\x7E])+')
        return ansi_escape.sub('', text)
    
    def update_progress(self, d):
        '''
        Info:
        ------
        Process to update the progress bar.
        '''
        #self.progress_bar.stop()
        #progress_str = d['_percent_str']
        #progress_percent = float(re.search(r'\d+\.\d+', progress_str).group())
        #self.progress_bar.config(mode='determinate', value=progress_percent)
        self.progress_bar.stop()

        # Remove the ANSI escape sequences and other non-printable characters
        data = {k: self.remove_ansi_escape_sequences(str(v)) for k, v in d.items()}
        
        if 'total_bytes' in data and 'downloaded_bytes' in data:
            total_bytes = int(data['total_bytes'])
            downloaded_bytes = int(data['downloaded_bytes'])
            percent = (downloaded_bytes / total_bytes) * 100
            
            progress_percent_str = d['_percent_str']
            progress_percent = float(re.search(r'\d+\.\d+', progress_percent_str).group())
            self.progress_bar.config(mode='determinate', value=progress_percent, maximum=100)
            
            speed = 'Unknown'
            if 'speed' in data and data['speed'] is not None:
                try:
                    speed = self.format_size(float(data['speed']))
                except (ValueError, TypeError):
                    speed = 'Unknown'
            
            eta = 'Unknown'
            if 'eta' in data and data['eta'] is not None:
                try:
                    eta = self.format_eta(int(data['eta']))
                except (ValueError, TypeError):
                    eta = 'Unknown'
            
            progress_message = f"{percent:.2f}% ({self.format_size(downloaded_bytes)}/{self.format_size(total_bytes)}) @ {speed}/s ETA: {eta}"
            #self.progress_label = ttk.Label(text=progress_message)
            #self.progress_label.grid(row=5, column=0)
            self.root.title(progress_message)
            
        if self.download_cancelled:
            raise Exception('Download cancelled.')

        
    def download_complete(self):
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate', value=100)
        self.show_message('Download completed successfully.')
        self.download_button.config(state='normal')
        self.cancel_button.config(state='disabled')
    
    def download_error(self):
        '''
        Error alert
        '''
        self.progress_bar.stop()
        self.show_message('Error occurred during the download.')
        self.download_button.config(state='normal')
        self.cancel_button.config(state='disabled')
    
    def select_output_directory(self):
        directory = filedialog.askdirectory(initialdir='/', title='Select output directory.')
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
    
    def cancel_download(self):
        '''
        Cancel alert
        '''
        self.stop_download_event.set()
        self.stop_search_event.set()
        self.progress_bar.stop()
        #self.show_message('Download canceled')
        self.download_button.config(state='normal')
        self.cancel_button.config(state='disabled')
    
            
    def download_with_progress(self, url, ydl_opts):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                #ydl.download([url])
                def hook(d):
                    if d['status'] == 'downloading' and self.stop_download_event.is_set():
                        ydl._progress_hooks.clear()  # Remove all progress hooks to stop the download
                        raise Exception('Download cancelled by user.')
                    self.progress_hook(d)
                ydl.add_progress_hook(hook)
                ydl.download([url])
        except Exception as e:
            self.show_message(f'Error during download: {str(e)}')
        finally:
            self.progress_bar.stop()
            self.download_button.config(state='normal')
            self.cancel_button.config(state='disabled')
            self.stop_download_event.clear()  # Clear the event for future use
            self.stop_search_event.clear()
            
    def show_message(self, message):
        tk.messagebox.showinfo('Info', message)
        
        
def main():
        root = tk.Tk()
        app = YtDownloaderApp(root)
        root.mainloop()
    
if __name__ == "__main__":
    main()