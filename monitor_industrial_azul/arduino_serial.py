import json,time
try: import serial
except ImportError: serial=None
class ArduinoReader:
    def __init__(self,port,baud=9600):
        if serial is None: raise RuntimeError("Instale pyserial: pip install pyserial")
        self.connection=serial.Serial(port,baud,timeout=.05); time.sleep(2); self.last_distance=None
    def read_distance(self):
        try:
            line=self.connection.readline().decode("utf-8",errors="ignore").strip()
            if line:
                obj=json.loads(line)
                if "distance_cm" in obj: self.last_distance=float(obj["distance_cm"])
        except (ValueError,json.JSONDecodeError): pass
        return self.last_distance
    def close(self):
        if self.connection and self.connection.is_open: self.connection.close()
