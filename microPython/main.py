# MicroPython (ESP32) - Conversión del código Arduino a MicroPython
# Asume placa ESP32. Pines ADC: 33, 32, 35, 25, 34.
# Pines dirección: 2, 4, 16, 17
# Pines PWM (enable): 5 y 18.
from machine import Pin, ADC, PWM
import time

# Pines de sensores (ADC)
sensorPin1 = 33  # Sensor izquierdo
sensorPin2 = 32  # Sensor central
sensorPin3 = 35  # Sensor derecho
sensorPin4 = 25  # Sensor derecho brusco
sensorPin5 = 34  # Sensor izquierdo brusco

# Pines del puente H (dirección)
motor1Pin1 = Pin(2, Pin.OUT)   # Motor izquierdo adelante
motor1Pin2 = Pin(4, Pin.OUT)   # Motor izquierdo atrás
motor2Pin1 = Pin(16, Pin.OUT)  # Motor derecho adelante
motor2Pin2 = Pin(17, Pin.OUT)  # Motor derecho atrás

# Pines PWM (velocidad / enable)
pwm_pin_left = PWM(Pin(5), freq=1000)
pwm_pin_right = PWM(Pin(18), freq=1000)

# Valores de velocidad (equivalentes a los del Arduino)
velMin = 74
velMedium = 77
velMax = 104

# Convertir valores 0-255 (Arduino) a 0-1023 (MicroPython PWM.duty)
def to_duty8bit_to_10bit(v):
    return int(v * 1023 / 255)

duty_min = to_duty8bit_to_10bit(velMin)
duty_medium = to_duty8bit_to_10bit(velMedium)
duty_max = to_duty8bit_to_10bit(velMax)

# Si la implementación de PWM en esta build usa duty_u16 en vez de duty(),
# adaptamos automáticamente.
use_duty_u16 = hasattr(pwm_pin_left, "duty_u16")

def set_pwm(pwm_obj, duty_10bit):
    if use_duty_u16:
        # map 0..1023 -> 0..65535
        pwm_obj.duty_u16(int(duty_10bit * 65535 // 1023))
    else:
        pwm_obj.duty(duty_10bit)

# Configurar ADCs
adc1 = ADC(Pin(sensorPin1))
adc2 = ADC(Pin(sensorPin2))
adc3 = ADC(Pin(sensorPin3))
adc4 = ADC(Pin(sensorPin4))
adc5 = ADC(Pin(sensorPin5))

# Configuraciones comunes para ESP32: 12-bit y atenuación para rango completo
for adc in (adc1, adc2, adc3, adc4, adc5):
    try:
        adc.width(ADC.WIDTH_12BIT)    # 0-4095
    except:
        pass
    try:
        adc.atten(ADC.ATTN_11DB)      # rango de entrada ampliado
    except:
        pass

THRESH = 1200  # Umbral usado en el código original

def stop_motors():
    motor1Pin1.value(0)
    motor1Pin2.value(0)
    motor2Pin1.value(0)
    motor2Pin2.value(0)
    set_pwm(pwm_pin_left, 0)
    set_pwm(pwm_pin_right, 0)

def forward_left_right(left_on, right_on, duty):
    # left_on, right_on: True/False para activar cada motor hacia adelante
    if left_on:
        motor1Pin1.value(1)
        motor1Pin2.value(0)
    else:
        motor1Pin1.value(0)
        motor1Pin2.value(0)

    if right_on:
        motor2Pin1.value(1)
        motor2Pin2.value(0)
    else:
        motor2Pin1.value(0)
        motor2Pin2.value(0)

    set_pwm(pwm_pin_left, duty)
    set_pwm(pwm_pin_right, duty)

# Inicializar velocidad a velMin
set_pwm(pwm_pin_left, duty_min)
set_pwm(pwm_pin_right, duty_min)

try:
    while True:
        izq = adc1.read()
        centro = adc2.read()
        der = adc3.read()
        izqBrusco = adc4.read()
        derBrusco = adc5.read()

        # Imprimir valores (serial por REPL)
        print("Izquierda:", izq,
              "| Centro:", centro,
              "| Derecha:", der,
              "| DerechaBrusco:", derBrusco,
              "| IzquierdaBrusco:", izqBrusco)

        # Lógica de seguimiento de línea (mismos umbrales y condiciones)
        if (centro < THRESH and izq > THRESH and der > THRESH and
                izqBrusco > THRESH and derBrusco > THRESH):
            # Sobre la línea -> avanzar recto
            forward_left_right(True, True, duty_min)

        elif (izq < THRESH and centro > THRESH and der > THRESH and
                  izqBrusco > THRESH and derBrusco > THRESH):
            # Girar a la izquierda suave: motor derecho detenido
            forward_left_right(True, False, duty_medium)

        elif (izq > THRESH and centro > THRESH and der < THRESH and
                  izqBrusco > THRESH and derBrusco > THRESH):
            # Girar a la derecha suave: motor izquierdo detenido
            forward_left_right(False, True, duty_medium)

        elif (izq > THRESH and centro > THRESH and der > THRESH and
                  izqBrusco > THRESH and derBrusco < THRESH):
            # Giro brusco a la derecha (derecha brusco detectado)
            forward_left_right(False, True, duty_max)

        elif (izq > THRESH and centro > THRESH and der > THRESH and
                  izqBrusco < THRESH and derBrusco > THRESH):
            # Giro brusco a la izquierda (izquierda brusco detectado)
            forward_left_right(True, False, duty_max)

        else:
            # Condición no contemplada: detener o mantener último estado (aquí detengo)
            stop_motors()

        time.sleep_ms(50)

except KeyboardInterrupt:
    stop_motors()
    print("Detenido por usuario")