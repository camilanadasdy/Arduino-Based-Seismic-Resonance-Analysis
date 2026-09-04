\begin{lstlisting}
#include <Wire.h>
#include <MPU6050.h>
MPU6050 mpu;
// Pines L298N
const int ENA = 9;
const int IN1 = 7;
const int IN2 = 8;
int pwmValue = 0;
// Control del experimento
bool experimentoActivo = false;
// Muestreo: 100 Hz
const unsigned long sampleInterval = 10;
unsigned long previousMillis = 0;
void setup() {
  Serial.begin(115200);
  Wire.begin();
  mpu.initialize();
  if (!mpu.testConnection()) {
    Serial.println("ERROR_MPU");
    while (true);}
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);
  Serial.println("ARDUINO_LISTO");}
void loop() {
  // ==========================
  // RECIBIR COMANDOS
  // ==========================
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    Serial.print("RECIBIDO -> ");
    Serial.println(comando);
    if (comando.startsWith("PWM:")) {
      pwmValue = comando.substring(4).toInt();
      pwmValue = constrain(pwmValue, 0, 255);
      analogWrite(ENA, pwmValue);
      Serial.print("PWM APLICADO -> ");
      Serial.println(pwmValue);

      if (pwmValue > 0) {

        experimentoActivo = true;

      } else {

        experimentoActivo = false;
      }    }}

  // ==========================
  // ADQUISICION DE DATOS
  // ==========================
  if (!experimentoActivo) {
    return;}

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= sampleInterval) {
    previousMillis = currentMillis;
    int16_t axRaw, ayRaw, azRaw;
    mpu.getAcceleration(
      &axRaw,
      &ayRaw,
      &azRaw);
    float ax = axRaw / 16384.0;
    float ay = ayRaw / 16384.0;
    float az = azRaw / 16384.0;
    Serial.print(currentMillis);
    Serial.print(",");
    Serial.print(ax, 4);
    Serial.print(",");
    Serial.print(ay, 4);
    Serial.print(",");
    Serial.print(az, 4);
    Serial.print(",");
    Serial.println(pwmValue); }}
