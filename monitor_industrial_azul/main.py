"""Painel demonstrativo de nivel de agua: camera RTSP + Arduino opcional."""
import argparse
import threading
import time
import cv2
import numpy as np
from camera_rtsp import RTSPCamera
from processamento_imagem import detect_waterline
from calculo_nivel import calculate_level
from armazenamento import save_measurement
from arduino_serial import ArduinoReader

W, H = 1320, 740
VIDEO = (20, 76, 652, 624)
PANEL_X = 674
BG = (26, 15, 5)        # BGR: azul-marinho
CARD = (45, 25, 8)
WHITE = (248, 246, 240)
MUTED = (208, 185, 158)
CYAN = (245, 189, 17)
GREEN = (110, 224, 50)
ORANGE = (28, 185, 249)
RED = (80, 80, 238)
BORDER = (212, 134, 0)

state = dict(roi=None, top=None, bottom=None, water=None, manual=False,
             pending=None, mapping=None, select_start=None, selecting=False,
             last_level=None, last_pct=None, last_arduino=None)

class BackgroundCamera:
    """Isola as operacoes bloqueantes RTSP da interface OpenCV."""
    def __init__(self, url, transport):
        self.url, self.transport = url, transport
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.frame = None
        self.received_at = 0
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        while not self.stop.is_set():
            camera = None
            try:
                camera = RTSPCamera(self.url, self.transport)
                while not self.stop.is_set():
                    frame = camera.read()
                    if frame is None:
                        break
                    with self.lock:
                        self.frame = frame
                        self.received_at = time.monotonic()
            except Exception as exc:
                print('RTSP:', exc)
            finally:
                if camera is not None:
                    camera.close()
            self.stop.wait(2)

    def snapshot(self):
        with self.lock:
            return (None if self.frame is None else self.frame.copy(), self.received_at)

    def close(self):
        self.stop.set()  # thread daemon pode terminar apos timeout de rede


def put(img, text, x, y, scale=.65, color=WHITE, thick=1):
    cv2.putText(img, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def panel_rect(img, x1, y1, x2, y2, color=CARD):
    cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)


def point_to_image(px, py):
    m = state['mapping']
    if m is None:
        return None
    x0, y0, dw, dh, fw, fh = m
    if not (x0 <= px < x0 + dw and y0 <= py < y0 + dh):
        return None
    return (min(fw-1, int((px-x0)*fw/dw)), min(fh-1, int((py-y0)*fh/dh)))


def mouse(event, x, y, flags, userdata):
    if event == cv2.EVENT_LBUTTONDOWN:
        p = point_to_image(x, y)
        if p is None:
            return
        if state['pending'] == 'roi':
            state['select_start'] = p
            state['selecting'] = True
        elif state['pending'] in ('top', 'bottom', 'water'):
            key = state['pending']
            state[key] = p[1]
            if key == 'water':
                state['manual'] = True
            state['pending'] = None
    elif event == cv2.EVENT_LBUTTONUP and state['selecting']:
        p = point_to_image(x, y)
        if p is not None:
            a = state['select_start']
            x1, x2 = sorted((a[0], p[0]))
            y1, y2 = sorted((a[1], p[1]))
            if x2-x1 >= 20 and y2-y1 >= 20:
                state['roi'] = (x1, y1, x2-x1, y2-y1)
                state['top'] = y1
                state['bottom'] = y2
                state['water'] = None
                state['manual'] = False
                state['pending'] = None
        state['selecting'] = False


def draw_video(canvas, frame):
    x1,y1,x2,y2 = VIDEO
    panel_rect(canvas, x1,y1,x2,y2, (13, 18, 26))
    state['mapping'] = None
    if frame is None:
        put(canvas, 'AGUARDANDO CAMERA RTSP', x1+90, (y1+y2)//2, .75, ORANGE, 2)
        return
    fh, fw = frame.shape[:2]
    scale = min((x2-x1-8)/fw, (y2-y1-8)/fh)
    dw, dh = max(1, round(fw*scale)), max(1, round(fh*scale))
    vx, vy = x1+(x2-x1-dw)//2, y1+(y2-y1-dh)//2
    img = cv2.resize(frame, (dw,dh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    canvas[vy:vy+dh, vx:vx+dw] = img
    state['mapping'] = (vx, vy, dw, dh, fw, fh)
    def y_screen(v): return vy+int(v*dh/fh)
    if state['roi']:
        rx, ry, rw, rh = state['roi']
        ax, ay = vx+int(rx*dw/fw), y_screen(ry)
        bx, by = vx+int((rx+rw)*dw/fw), y_screen(ry+rh)
        cv2.rectangle(canvas, (ax,ay), (bx,by), CYAN, 2)
    for key, label, color in [('top','100%',GREEN), ('bottom','0%',ORANGE), ('water','AGUA',CYAN)]:
        if state[key] is not None:
            yy = y_screen(state[key])
            cv2.line(canvas, (vx,yy), (vx+dw-1,yy), color, 2)
            put(canvas, label, vx+9, max(vy+19, yy-8), .56, color, 2)
    if state['selecting'] and state['select_start']:
        put(canvas, 'Arraste ate o outro canto do recipiente', vx+10, vy+30, .55, WHITE, 2)


def box_outline(img, x1, y1, x2, y2, color=BORDER):
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)


def draw_dashboard(frame, online, level, pct, distance, height, arduino_enabled=False, manual=False):
    canvas = np.full((H, W, 3), BG, np.uint8)
    # Painel esquerdo: sem cabecalho geral, video e teclas preservadas
    panel_rect(canvas, 16, 16, 662, 722)
    box_outline(canvas, 16, 16, 662, 722)
    put(canvas, 'CAMERA AO VIVO', 35, 51, .85, WHITE, 2)
    put(canvas, 'RTSP ONLINE' if online else 'RTSP OFFLINE', 495, 50, .58, GREEN if online else RED, 2)
    draw_video(canvas, frame)
    put(canvas, 'R  Selecionar', 35, 660, .54, CYAN)
    put(canvas, 'T  Topo (100%)', 195, 660, .54, WHITE)
    put(canvas, 'B  Fundo (0%)', 395, 660, .54, WHITE)
    put(canvas, 'M  Agua', 35, 694, .54, WHITE)
    put(canvas, 'A  Auto / Manual', 195, 694, .54, WHITE)
    put(canvas, 'S  Salvar CSV', 430, 694, .54, WHITE)
    # Painel direito: caixa d'agua 2D e graduacao de 10 em 10
    panel_rect(canvas, 680, 16, 1303, 509)
    box_outline(canvas, 680, 16, 1303, 509)
    put(canvas, "NIVEL DA CAIXA D'AGUA", 705, 53, .81, WHITE, 2)
    cv2.line(canvas, (702, 68), (1280, 68), BORDER, 1)
    tx1, ty1, tx2, ty2 = 764, 119, 1020, 466
    panel_rect(canvas, tx1, ty1, tx2, ty2, (62, 34, 12))
    if pct is not None:
        fill = max(0.0, min(100.0, pct)) / 100
        fill_y = int(ty2 - fill * (ty2 - ty1))
        cv2.rectangle(canvas, (tx1+3, fill_y), (tx2-3, ty2-3), (220, 147, 5), -1)
    box_outline(canvas, tx1, ty1, tx2, ty2, WHITE)
    for n in range(0, 101, 10):
        y = round(ty2 - n / 100 * (ty2-ty1))
        cv2.line(canvas, (tx1+1, y), (tx2-1, y), (190, 153, 111), 1)
        put(canvas, f'{n:>3}%', 700, y+5, .43, MUTED)
    put(canvas, 'NIVEL ATUAL', 1040, 123, .58, MUTED)
    put(canvas, f'{pct:.1f}%' if pct is not None else '--.-%', 1040, 191, 1.25, CYAN, 3)
    cv2.line(canvas, (1040, 211), (1279, 211), BORDER, 1)
    put(canvas, 'ALTURA DA AGUA', 1040, 248, .52, MUTED)
    put(canvas, f'{level:.1f} cm' if level is not None else '-- cm', 1040, 293, .95, WHITE, 2)
    cv2.line(canvas, (1040, 315), (1279, 315), BORDER, 1)
    put(canvas, 'ALTURA CONFIGURADA', 1040, 351, .47, MUTED)
    put(canvas, f'{height:.1f} cm', 1040, 396, .95, WHITE, 2)
    put(canvas, 'MODO: MANUAL' if manual else 'MODO: AUTOMATICO', 1040, 453, .43, ORANGE if manual else GREEN)
    # Area Arduino: estado funcional, com dados quando recebidos
    panel_rect(canvas, 680, 522, 1303, 612)
    box_outline(canvas, 680, 522, 1303, 612)
    put(canvas, 'ARDUINO / HC-SR04', 702, 557, .68, WHITE, 2)
    if distance is not None:
        put(canvas, f'CONECTADO  |  DISTANCIA: {distance:.1f} cm', 702, 592, .65, GREEN, 2)
    elif arduino_enabled:
        put(canvas, 'PORTA CONFIGURADA - AGUARDANDO LEITURA', 702, 592, .53, ORANGE, 2)
    else:
        put(canvas, 'DESCONECTADO  |  USE --port COM3', 702, 592, .57, MUTED)
    panel_rect(canvas, 680, 624, 1303, 722)
    box_outline(canvas, 680, 624, 1303, 722)
    if not online:
        status = 'SEM SINAL DA CAMERA'
        detail = 'Confira o OctoStream e a conexao RTSP.'
        color = RED
    elif pct is None:
        status = 'AGUARDANDO CALIBRACAO'
        detail = 'R: selecionar | T: topo | B: fundo | M: agua'
        color = ORANGE
    else:
        status = 'MONITORAMENTO ATIVO'
        detail = 'Estimativa pela camera; confirme a linha de agua.'
        color = GREEN
    put(canvas, status, 704, 664, .75, color, 2)
    put(canvas, detail, 704, 696, .57, WHITE)
    if state['pending']:
        put(canvas, 'CLIQUE NA IMAGEM: ' + state['pending'].upper(), 700, 716, .42, ORANGE)
    return canvas

def main():
    parser = argparse.ArgumentParser(description='Painel industrial de nivel de agua')
    parser.add_argument('--rtsp', required=True)
    parser.add_argument('--transport', choices=['tcp','udp'], default='udp')
    parser.add_argument('--height-cm', type=float, default=30.0)
    parser.add_argument('--port', default='', help='Porta serial do Arduino, ex. COM3')
    parser.add_argument('--baud', type=int, default=9600)
    args = parser.parse_args()
    if args.height_cm <= 0:
        parser.error('--height-cm deve ser maior que zero')
    camera = BackgroundCamera(args.rtsp, args.transport)
    uno = ArduinoReader(args.port, args.baud) if args.port else None
    window = 'MONITOR INDUSTRIAL - Nivel de agua'
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, W, H)
    cv2.setMouseCallback(window, mouse)
    print('R: selecionar recipiente | T: topo | B: fundo | M: agua | A: automatico/manual | S: CSV | Q: sair')
    last_detect = 0
    try:
        while True:
            frame, received_at = camera.snapshot()
            online = frame is not None and time.monotonic() - received_at < 3
            if not online:
                frame = None
            if online and state['roi'] is not None and not state['manual'] and time.monotonic()-last_detect >= .15:
                found = detect_waterline(frame, state['roi'])
                if found is not None:
                    state['water'] = found
                last_detect = time.monotonic()
            level, pct = calculate_level(state['top'], state['bottom'], state['water'], args.height_cm)
            if not online:
                level, pct = None, None  # nao exibir medida antiga como atual
            distance = uno.read_distance() if uno else None
            canvas = draw_dashboard(frame, online, level, pct, distance, args.height_cm, bool(args.port), state['manual'])
            cv2.imshow(window, canvas)
            key = cv2.waitKey(30) & 255
            if key in (ord('q'), 27):
                break
            elif key == ord('r'):
                state['pending'] = 'roi'
            elif key == ord('t'):
                state['pending'] = 'top'
            elif key == ord('b'):
                state['pending'] = 'bottom'
            elif key == ord('m'):
                state['pending'] = 'water'
            elif key == ord('a'):
                state['manual'] = not state['manual']
            elif key == ord('s'):
                save_measurement(level, pct, 'manual' if state['manual'] else 'camera', distance)
                print('Salvo em medicoes.csv')
            try:
                if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break
    finally:
        camera.close()
        if uno:
            uno.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
