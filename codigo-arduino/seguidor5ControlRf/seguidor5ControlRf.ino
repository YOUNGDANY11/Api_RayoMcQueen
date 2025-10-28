

const int sensorPin1 = 33;  // Sensor izquierdo
const int sensorPin2 = 32;  // Sensor central
const int sensorPin3 = 35;  // Sensor derecho
const int sensorPin4 = 25;  // Sensor derecho bruzco
const int sensorPin5 = 34; /// Sensor izquierdo bruzco
// Sensor izquierdo

const int motor1Pin1 = 2;   // Motor izquierdo adelante
const int motor1Pin2 = 4;   // Motor izquierdo atrás
const int motor2Pin1 = 16;   // Motor derecho adelante
const int motor2Pin2 = 17;   // Motor derecho atrás
int velMin = 74, velMedium = 77 , velMax = 104;// motor n20 2000 rpm
//int velMin = 78, velMedium = 80, velMax = 110;
//int velMin = 150, velMedium = 160, velMax = 168;
// Configuración inicial
void setup() {
  // Iniciar la comunicación serial
 //Serial.begin(9600);

  // Configurar lllllllllllllllllllpines de los sensores
  pinMode(sensorPin1, INPUT);
  pinMode(sensorPin2, INPUT);
  pinMode(sensorPin3, INPUT);
  pinMode(sensorPin4, INPUT);
  pinMode(sensorPin5, INPUT);
  // Configurar pines del puente H para motores
  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(motor2Pin1, OUTPUT);
  pinMode(motor2Pin2, OUTPUT);


  // Configurar pines de velocidad
  pinMode(5, OUTPUT);
  pinMode(18, OUTPUT);
  analogWrite(5, velMin);  // Configurar la velocidad inicial
  analogWrite(18, velMin);
}

// Bucle principal
void loop() {
    // Leer los valores de los sensores
    int izq = analogRead(sensorPin1);
    int centro = analogRead(sensorPin2);
    int der = analogRead(sensorPin3);
    int izqBrusco = analogRead(sensorPin4);
    int derBrusco = analogRead(sensorPin5);

    // Imprimir los valores de los sensores en el monitor serial

    Serial.print("Izquierda: ");
    Serial.print(izq);
    Serial.print(" | Centro: ");
    Serial.print(centro);
    Serial.print(" | Derecha: ");
    Serial.print(der);
    Serial.print(" | DerechaBrusco: ");
    Serial.print(derBrusco);
    Serial.print(" | izquierdaBrusco: ");
    Serial.println(izqBrusco);

    // Lógica de seguimiento de línea
    if (centro < 1200 && izq > 1200 && der > 1200 && izqBrusco > 1200 && derBrusco > 1200 ) {// El robot está sobre la línea, avanzar recto
      digitalWrite(motor1Pin1, HIGH);
      digitalWrite(motor1Pin2, LOW);
      digitalWrite(motor2Pin1, HIGH);
      digitalWrite(motor2Pin2, LOW);
      analogWrite(5, velMin);  // Velocidad estándar
      analogWrite(18, velMin);
    } else if (izq < 1200 && centro > 1200 && der > 1200 && izqBrusco > 1200 && derBrusco > 1200) {//izq
      digitalWrite(motor1Pin1, HIGH);
      digitalWrite(motor1Pin2, LOW);
      digitalWrite(motor2Pin1, LOW);
      digitalWrite(motor2Pin2, LOW);
      analogWrite(5, velMedium);  // Reducción de velocidad para girar
      analogWrite(18, velMedium);
   
  } else if (izq > 1200 && centro >1200 && der < 1200 && izqBrusco > 1200 && derBrusco > 1200) {//der
      digitalWrite(motor1Pin1, LOW);
      digitalWrite(motor1Pin2, LOW);
      digitalWrite(motor2Pin1, HIGH);
      digitalWrite(motor2Pin2, LOW);
      analogWrite(5, velMedium);
      analogWrite(18,velMedium);  // Reducción de velocidad para girar

  }
  else if (izq > 1200 && centro > 1200 && der > 1200 && izqBrusco > 1200 && derBrusco < 1200) {//derechaBrusco
     digitalWrite(motor1Pin1, LOW);
      digitalWrite(motor1Pin2, LOW);
      digitalWrite(motor2Pin1, HIGH);
      digitalWrite(motor2Pin2, LOW);
      analogWrite(5, velMax);  // Reducción de velocidad para girar
      analogWrite(18, velMax);

  }else if (izq > 1200 && centro > 1200 && der > 1200 && izqBrusco < 1200 && derBrusco >1200) {//izquierdaBrusco  
      digitalWrite(motor1Pin1, HIGH);
      digitalWrite(motor1Pin2, LOW);
      digitalWrite(motor2Pin1, LOW);
      digitalWrite(motor2Pin2, LOW);
      analogWrite(5, velMax);
      analogWrite(18,velMax);  // Reducción de velocidad para girar
  }
} 