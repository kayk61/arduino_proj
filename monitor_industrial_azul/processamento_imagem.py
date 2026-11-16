import cv2, numpy as np
def detect_waterline(frame,roi):
    """Detector experimental de borda horizontal dentro da regiao selecionada."""
    x,y,w,h=roi
    crop=frame[y:y+h,x:x+w]
    if crop.size==0 or h<30 or w<30: return None
    gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
    gray=cv2.GaussianBlur(gray,(5,5),0)
    grad=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
    profile=np.mean(np.abs(grad),axis=1)
    profile=np.convolve(profile,np.ones(9,dtype=np.float32)/9,mode="same")
    lo,hi=int(h*.08),int(h*.92)
    if hi<=lo: return None
    pos=lo+int(np.argmax(profile[lo:hi]))
    return y+pos if float(profile[pos])>=2.0 else None
