import os, cv2
class RTSPCamera:
    def __init__(self,url,transport="tcp"):
        if not url.lower().startswith(("rtsp://","rtsps://")):
            raise ValueError("A URL precisa comecar com rtsp:// ou rtsps://")
        self.url,self.transport=url,transport
        self.cap=None
        self._open()
    def _open(self):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]=f"rtsp_transport;{self.transport}"
        self.cap=cv2.VideoCapture(self.url,cv2.CAP_FFMPEG)
        if self.cap.isOpened(): self.cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
    def read(self):
        if self.cap is None or not self.cap.isOpened(): return None
        ok,frame=self.cap.read()
        return frame if ok else None
    def reconnect(self):
        self.close(); self._open()
    def close(self):
        if self.cap is not None: self.cap.release(); self.cap=None
