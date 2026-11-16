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

A porta COM3 e apenas exemplo. Feche o Monitor Serial do Arduino IDE. Para calcular porcentagem com o sensor, informe tambem --empty-distance-cm e --full-distance-cm conforme o exemplo abaixo.

## Limitacoes importantes
- O detector automatico e experimental. Vidro transparente, reflexos, fundo e movimento podem confundir a linha d'agua. Confira visualmente se a linha acompanha a superficie; em modo manual, a medida fica fixa ate novo clique.
- O percentual representa a altura, nao necessariamente o volume para copos de formato irregular.
- Nao use como unico sistema de seguranca para transbordamento ou acionamento de bombas.
- A imagem nao e esticada: e exibida mantendo sua proporcao.

## MODO NOVO: ARDUINO CONTROLA A PORCENTAGEM AUTOMATICAMENTE
O sensor deve ficar fixo acima da agua, apontado para baixo. Antes de executar, meca em centimetros:
- `--empty-distance-cm`: distancia do sensor ate a superficie (ou fundo refletor) quando o recipiente esta VAZIO.
- `--full-distance-cm`: distancia do sensor ate a superficie quando esta CHEIO.
A distancia VAZIO precisa ser maior que CHEIO. Use valores reais, nao os exemplos.

Exemplo apenas ilustrativo, para vazio=15 cm e cheio=3 cm, altura util=12 cm:

`py main.py --rtsp "rtsp://192.168.18.2:554/stream" --transport udp --height-cm 12 --port COM3 --empty-distance-cm 15 --full-distance-cm 3`

Ao usar `--port`, o HC-SR04 passa a ser a FONTE da porcentagem e do preenchimento da caixa-d'agua; a camera fica so como imagem ao vivo. Mesmo sem imagem RTSP, o sensor pode continuar indicando o nivel. Sem `--port`, o programa usa o metodo anterior da camera. Se a leitura do Arduino parar por 3 segundos, o nivel fica indisponivel em vez de congelar uma leitura antiga.

O arquivo .ino continua enviando `distance_cm` em JSON a 9600 baud. Grave-o no Arduino IDE, feche o Monitor Serial e use a porta COM correta. O sensor HC-SR04 comum nao e impermeavel e pode falhar com vapor, espuma ou reflexos. Nao use para acionar bomba ou impedir transbordamento sem protecoes independentes.

## NOVO: LINHA DA CAMERA ACOMPANHA O ARDUINO
Com --port e calibracao das distancias, o Arduino calcula o nivel e move a linha ciano AGUA (HC-SR04) sobre a imagem da camera.
1. Abra o video RTSP e conecte o Arduino.
2. Pressione R e arraste para selecionar o recipiente: isso marca topo e fundo iniciais.
3. Se necessario, pressione T e clique no ponto da imagem que corresponde a 100%; pressione B e clique no ponto de 0%.
4. A linha ciano acompanha a porcentagem do HC-SR04, subindo quando a agua sobe e descendo quando a agua desce.
5. Em modo Arduino, M e A nao mudam a linha do sensor. Sem Arduino, as funcoes de camera anteriores continuam.
6. Se o sensor ficar sem leitura recente, a linha ciano desaparece (nao congela um valor antigo).
A linha e uma projecao da medida do sensor no video, nao uma deteccao visual da superficie. Mantenha camera e sensor fixos e calibração consistente.
