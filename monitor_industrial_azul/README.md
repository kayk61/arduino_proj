# Monitor industrial azul - camera RTSP + Arduino opcional

## Instalar
Abra CMD nesta pasta e execute `py -m pip install -r requirements.txt`.

## Executar so com iPhone
Mantenha o OctoStream aberto no iPhone e execute:

`py main.py --rtsp "rtsp://192.168.18.2:554/stream" --transport udp --height-cm 12`

Substitua 12 pela altura util REAL do recipiente em centimetros. A URL pode mudar conforme o OctoStream.

## Calibrar
- R: selecione o recipiente arrastando o mouse na imagem (sem pressionar Enter).
- T: pressione T e clique na altura que representa 100%.
- B: pressione B e clique na altura que representa 0%.
- M: pressione M e clique na superficie (modo manual).
- A: alterna entre modo manual e automatico.
- S: salva CSV.
- Q ou ESC: fecha.

A caixa d'agua 2D no lado direito preenche conforme a porcentagem estimada. A escala tem marcas de 10 em 10%.

## Com Arduino Uno (opcional)
Conecte HC-SR04: VCC->5V, GND->GND, TRIG->D9, ECHO->D10. Carregue `arduino/arduino_uno_hcsr04_monitor.ino` no Arduino IDE e conecte USB ao PC. Identifique a porta serial e execute:

`py main.py --rtsp "rtsp://192.168.18.2:554/stream" --transport udp --height-cm 12 --port COM3`

A porta COM3 e apenas exemplo. Feche o Monitor Serial do Arduino IDE. O painel exibe a distancia do HC-SR04, mas a porcentagem continua sendo estimada pela camera; a conversao do sensor em porcentagem exige calibracao adicional.

## Limitacoes importantes
- O detector automatico e experimental. Vidro transparente, reflexos, fundo e movimento podem confundir a linha d'agua. Confira visualmente se a linha acompanha a superficie; em modo manual, a medida fica fixa ate novo clique.
- O percentual representa a altura, nao necessariamente o volume para copos de formato irregular.
- Nao use como unico sistema de seguranca para transbordamento ou acionamento de bombas.
- A imagem nao e esticada: e exibida mantendo sua proporcao.
