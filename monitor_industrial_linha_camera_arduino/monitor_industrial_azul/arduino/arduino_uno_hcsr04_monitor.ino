const int TRIG = 9;
const int ECHO = 10;

void setup() {
  Serial.begin(9600);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
}

void loop() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  unsigned long duracao = pulseIn(ECHO, HIGH, 30000UL);
  if (duracao > 0) {
    float distancia = duracao * 0.0343 / 2.0;
    Serial.print("{\"distance_cm\":");
    Serial.print(distancia, 2);
    Serial.println("}");
  }
  delay(500);
}
