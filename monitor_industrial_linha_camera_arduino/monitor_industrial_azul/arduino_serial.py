import json,time
try: import serial
except ImportError: serial=None
class ArduinoReader:
    def __init__(self,port,baud=9600):
        if serial is None: raise RuntimeError("Instale pyserial: pip install pyserial")
        self.connection=serial.Serial(port,baud,timeout=.05); time.sleep(2); self.last_distance=None; self.last_at=0
    def read_distance(self):
        try:
            line=self.connection.readline().decode("utf-8",errors="ignore").strip()
            if line:
                obj=json.loads(line)
                if "distance_cm" in obj: self.last_distance=float(obj["distance_cm"]); self.last_at=time.monotonic()
        except (ValueError,json.JSONDecodeError): pass
        return self.last_distance
    def is_fresh(self):
        return self.last_distance is not None and time.monotonic()-self.last_at < 3.0
    def close(self):
        if self.connection and self.connection.is_open: self.connection.close()
