from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtWebChannel import QWebChannel
from pathlib import Path
import sys
import os

from backend_worker import vid_downloader_backend
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.browser = QWebEngineView()
        self.channel = QWebChannel(self.browser.page())
        self.backend = vid_downloader_backend()
        self.channel.registerObject('backend', self.backend)
        
        # Used to compile with pyinstaller.
        if hasattr(sys, '_MEIPASS'):
            # when compiled with the pyinstaller will be in the folder _MEIPASS
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path.cwd()
        file_path = base_path / "resources" / "index.html"
        
        # Loads the HTML for the frontend.
        if file_path.exists():
            url_path = file_path.as_uri()
            url = QUrl(url_path)
            self.browser.setUrl(url)
            self.browser.page().setWebChannel(self.channel)
        #url = QUrl("file:///resources/index.html")
        #self.browser.setUrl(url)
        else: 
            print('Index was not found')
        
        # Define widow size and name.
        self.setCentralWidget(self.browser)
        self.setGeometry(100, 100, 750, 550)
        self.setWindowTitle("YouTube Video Downloader")

        # Response after loading the frontend.
        self.browser.loadFinished.connect(self.on_load_finished)
        
        # Add the DevTools button, debugging purposes don't forget to uncomment the mouse right click block in javascript.
        # dev_tools_action = QAction('Open DevTools', self)
        # dev_tools_action.triggered.connect(self.open_dev_tools)
        # self.menuBar().addAction(dev_tools_action)
    
    def on_load_finished(self):
        print("FrontEnd successfully loaded")
    def closeEvent(self, event):
        self.backend.close_app() # From backend call the close_app with the cancel_download integrated.
        event.accept()
        
    def open_dev_tools(self):
        # Create an window for the the DevTools
        dev_tools_window = QMainWindow(self)
        dev_tools_browser = QWebEngineView(dev_tools_window)
        dev_tools_browser.page().setUrl(QUrl("about:blank"))
        
        # Open DevTools in an new window.
        dev_tools_window.setCentralWidget(dev_tools_browser)
        dev_tools_window.resize(800, 600)
        dev_tools_window.setWindowTitle("DevTools")
        dev_tools_window.show()

        # Connect the DevTools to the initial page.
        self.browser.page().setDevToolsPage(dev_tools_browser.page())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = App()
    mainWin.show()
    sys.exit(app.exec_())