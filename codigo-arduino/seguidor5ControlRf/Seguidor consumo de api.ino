#include <WiFi.h>
#include <HTTPClient.h>

// --- Pines de sensores (ADC1, compatibles con WiFi) ---
#define SENSOR_IZQ      33  // D33
#define SENSOR_CENTRO   32  // D32
#define SENSOR_DER      35  // D35
#define SENSOR_DER_BR   34  // D34

// --- Pines de motores ---
#define MOTOR1_ADELANTE 2
#define MOTOR1_ATRAS    4
#define MOTOR2_ADELANTE 16
#define MOTOR2_ATRAS    17

#define PWM_LEFT        5
#define PWM_RIGHT       18

// --- WiFi y API ---
const char* ssid     = "Familia_Morales";
const char* password = "2811LIMADA";
const char* apiUrl   = "http://192.168.1.8:3000/api/cart/instrucciones";
const char* apiControlUrl = "http://192.168.1.8:3000/api/control/accion"; // Nueva API para control remoto

String instruccion = "";      // Acción actual
String ultimaInstruccion = ""; // Última instrucción enviada
bool carritoActivo = true;     // Estado del carrito desde el control remoto

void setup() {
  Serial.begin(115200);

  pinMode(SENSOR_IZQ, INPUT);
  pinMode(SENSOR_CENTRO, INPUT);
  pinMode(SENSOR_DER, INPUT);
  pinMode(SENSOR_DER_BR, INPUT);

  pinMode(MOTOR1_ADELANTE, OUTPUT);
  pinMode(MOTOR1_ATRAS, OUTPUT);
  pinMode(MOTOR2_ADELANTE, OUTPUT);
  pinMode(MOTOR2_ATRAS, OUTPUT);

  pinMode(PWM_LEFT, OUTPUT);
  pinMode(PWM_RIGHT, OUTPUT);

  // Conexión WiFi
  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
}

void enviarInstruccion(const String& accion) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(apiUrl);
    http.addHeader("Content-Type", "application/json");
    String payload = "{\"instruccion\":\"" + accion + "\"}";
    int httpResponseCode = http.POST(payload);
    Serial.print("Enviado: ");
    Serial.print(payload);
    Serial.print(" | Código HTTP: ");
    Serial.println(httpResponseCode);
    http.end();
  } else {
    Serial.println("WiFi no conectado para enviar instruccion.");
  }
}

// Consulta el estado del carrito
void consultarControlRemoto() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(apiControlUrl);
    int httpCode = http.GET();
    if (httpCode == 200) {
      String payload = http.getString();
      // Debe contener "arrancar" o "detener" como texto simple o en JSON
      if (payload.indexOf("arrancar") != -1) carritoActivo = true;
      else if (payload.indexOf("detener") != -1) carritoActivo = false;
      Serial.print("Control remoto recibido: ");
      Serial.println(payload);
    }
    http.end();
  }
}

// Funciones de control motor
void motoresRecto() {
  digitalWrite(MOTOR1_ADELANTE, HIGH);
  digitalWrite(MOTOR1_ATRAS, LOW);
  digitalWrite(MOTOR2_ADELANTE, HIGH);
  digitalWrite(MOTOR2_ATRAS, LOW);
  analogWrite(PWM_LEFT, 80);
  analogWrite(PWM_RIGHT, 80);
}
void motoresIzquierda() {
  digitalWrite(MOTOR1_ADELANTE, HIGH);
  digitalWrite(MOTOR1_ATRAS, LOW);
  digitalWrite(MOTOR2_ADELANTE, LOW);
  digitalWrite(MOTOR2_ATRAS, LOW);
  analogWrite(PWM_LEFT, 70);
  analogWrite(PWM_RIGHT, 70);
}
void motoresDerecha() {
  digitalWrite(MOTOR1_ADELANTE, LOW);
  digitalWrite(MOTOR1_ATRAS, LOW);
  digitalWrite(MOTOR2_ADELANTE, HIGH);
  digitalWrite(MOTOR2_ATRAS, LOW);
  analogWrite(PWM_LEFT, 70);
  analogWrite(PWM_RIGHT, 70);
}
void motoresDerechaBrusco() {
  digitalWrite(MOTOR1_ADELANTE, LOW);
  digitalWrite(MOTOR1_ATRAS, LOW);
  digitalWrite(MOTOR2_ADELANTE, HIGH);
  digitalWrite(MOTOR2_ATRAS, LOW);
  analogWrite(PWM_LEFT, 100);
  analogWrite(PWM_RIGHT, 100);
}
void motoresDetener() {
  digitalWrite(MOTOR1_ADELANTE, LOW);
  digitalWrite(MOTOR1_ATRAS, LOW);
  digitalWrite(MOTOR2_ADELANTE, LOW);
  digitalWrite(MOTOR2_ATRAS, LOW);
  analogWrite(PWM_LEFT, 0);
  analogWrite(PWM_RIGHT, 0);
}

void loop() {
  consultarControlRemoto(); // consulta el estado remoto

  if (!carritoActivo) {
    motoresDetener();
    instruccion = "detener";
    if (instruccion != ultimaInstruccion) {
      enviarInstruccion(instruccion);
      ultimaInstruccion = instruccion;
    }
    delay(200);
    return;
  }

  int izq      = analogRead(SENSOR_IZQ);
  int centro   = analogRead(SENSOR_CENTRO);
  int der      = analogRead(SENSOR_DER);
  int derBr    = analogRead(SENSOR_DER_BR);

  Serial.printf("Izq:%d Centro:%d Der:%d DerBr:%d\n", izq, centro, der, derBr);

  // --- Lógica básica seguidor de línea ---
  if (centro < 1200 && izq > 1200 && der > 1200 && derBr > 1200) {
    instruccion = "recto";
    motoresRecto();
  } else if (izq < 1200 && centro > 1200 && der > 1200 && derBr > 1200) {
    instruccion = "izquierda";
    motoresIzquierda();
  } else if (izq > 1200 && centro > 1200 && der < 1200 && derBr > 1200) {
    instruccion = "derecha";
    motoresDerecha();
  } else if (izq > 1200 && centro > 1200 && der > 1200 && derBr < 1200) {
    instruccion = "derechaBrusco";
    motoresDerechaBrusco();
  } else {
    instruccion = "detener";
    motoresDetener();
  }

  // Solo enviar si la instruccion cambió
  if (instruccion != ultimaInstruccion) {
    enviarInstruccion(instruccion);
    ultimaInstruccion = instruccion;
  }

  delay(50);
}