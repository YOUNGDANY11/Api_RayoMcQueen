# MicroPython Line Follower ESP32 + L298N + HW-871 (5 sensores)
# Modificado para registrar acciones y velocidad en API (/api/instrucciones)
# Mantiene la misma estructura original, con llamadas a la API añadidas.
# Rellenar WIFI_SSID, WIFI_PASS y API_URL antes de usar.

import time
import ujson
import network
try:
    import urequests as requests
except Exception:
    # Si tu build tiene requests con otro nombre, ajústalo
    import requests

from machine import Pin, PWM

# ========= CONFIGURACIÓN =========
# El típico LM393 da LOW sobre negro. Cambia a False si en tu módulo es al revés.
BLACK_RETURNS_LOW = True

# Dirección global del robot: 1 = hacia delante; -1 = invertido
DRIVE_DIR = -1

# Pines L298N (verifica motor asignado)
PIN_ENA = 18  # Motor derecho
PIN_IN1 = 17
PIN_IN2 = 16

PIN_ENB = 5   # Motor izquierdo
PIN_IN3 = 4
PIN_IN4 = 2

# Sensores (izq -> der)
SENSOR_PINS = [34, 35, 32, 33, 25]
CENTER_INDEX = 2  # sensor central (GPIO32)

# PWM (bajamos a 1 kHz para más par a baja velocidad en L298N)
PWM_FREQ_HZ = 1000

# Velocidades
BASE_SPEED = 0.70         # recto cuando el central ve negro
TURN_SPEED = 0.80         # velocidad del motor opuesto cuando se apaga el del lado que ve negro
CRUISE_WHEN_LOST = 0.35   # avance suave cuando ningún sensor ve negro

# Patada de arranque para vencer inercia al pasar de 0 a >0
KICK_MS = 60
KICK_LEVEL = 1.0

# Sobremuestreo de sensores para estabilidad
OVERSAMPLE = 3
OVERSAMPLE_DELAY_MS = 1

# Test de motores al iniciar (recomendado la primera vez)
RUN_MOTOR_TEST_ON_BOOT = True

# Depuración
DEBUG = False

# ========= API / WIFI =========
WIFI_SSID = "Familia_Morales"
WIFI_PASS = "2811LIMADA"
# Ejemplo: "http://192.168.1.50:3000/api/instrucciones"
API_URL = "http://192.168.1.23:3000/api/instrucciones"
API_TIMEOUT_S = 3

# ========= UTILIDADES =========
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def set_pwm_0_1(pwm, value_0_1):
    duty16 = int(clamp(value_0_1, 0.0, 1.0) * 65535)
    try:
        pwm.duty_u16(duty16)
    except AttributeError:
        pwm.duty(int(duty16 * 1023 / 65535))


class Motor:
    def __init__(self, pin_in1, pin_in2, pin_en, invert=False, pwm_freq=PWM_FREQ_HZ):
        self.in1 = Pin(pin_in1, Pin.OUT)
        self.in2 = Pin(pin_in2, Pin.OUT)
        self.pwm = PWM(Pin(pin_en), freq=pwm_freq)
        self.invert = invert
        self.stop()

    def forward(self):
        if not self.invert:
            self.in1.value(1)
            self.in2.value(0)
        else:
            self.in1.value(0)
            self.in2.value(1)

    def backward(self):
        if not self.invert:
            self.in1.value(0)
            self.in2.value(1)
        else:
            self.in1.value(1)
            self.in2.value(0)

    def stop(self):
        self.in1.value(0)
        self.in2.value(0)
        set_pwm_0_1(self.pwm, 0.0)

    def set_speed_forward_0_1(self, speed_0_1):
        s = clamp(speed_0_1, 0.0, 1.0)
        self.forward()
        set_pwm_0_1(self.pwm, s)

    def set_speed_backward_0_1(self, speed_0_1):
        s = clamp(speed_0_1, 0.0, 1.0)
        self.backward()
        set_pwm_0_1(self.pwm, s)


# ========= INICIALIZACIÓN =========
right_motor = Motor(PIN_IN1, PIN_IN2, PIN_ENA, invert=False, pwm_freq=PWM_FREQ_HZ)
left_motor  = Motor(PIN_IN3, PIN_IN4, PIN_ENB, invert=False, pwm_freq=PWM_FREQ_HZ)

sensor_pins = [Pin(p, Pin.IN) for p in SENSOR_PINS]

_last_L = 0.0
_last_R = 0.0


def is_black_level(level):
    return (level == 0) if BLACK_RETURNS_LOW else (level == 1)


def read_sensors_black_once():
    raw = [pin.value() for pin in sensor_pins]
    return [is_black_level(v) for v in raw], raw


def read_sensors_black_stable(oversample=OVERSAMPLE, delay_ms=OVERSAMPLE_DELAY_MS):
    counts = [0] * 5
    last_raw = None
    for _ in range(max(1, oversample)):
        blacks, last_raw = read_sensors_black_once()
        for i, b in enumerate(blacks):
            if b:
                counts[i] += 1
        if delay_ms:
            time.sleep_ms(delay_ms)
    threshold = (oversample // 2) + 1
    blacks_stable = [c >= threshold for c in counts]
    return blacks_stable, last_raw


def set_wheel_speeds_forward(left_0_1, right_0_1):
    global _last_L, _last_R

    l = clamp(left_0_1, 0.0, 1.0)
    r = clamp(right_0_1, 0.0, 1.0)

    # Patada de arranque al pasar de 0 -> >0
    if DRIVE_DIR >= 0:
        if _last_L == 0.0 and l > 0.0:
            left_motor.set_speed_forward_0_1(KICK_LEVEL)
            time.sleep_ms(KICK_MS)
        if _last_R == 0.0 and r > 0.0:
            right_motor.set_speed_forward_0_1(KICK_LEVEL)
            time.sleep_ms(KICK_MS)

        left_motor.set_speed_forward_0_1(l)
        right_motor.set_speed_forward_0_1(r)
    else:
        if _last_L == 0.0 and l > 0.0:
            left_motor.set_speed_backward_0_1(KICK_LEVEL)
            time.sleep_ms(KICK_MS)
        if _last_R == 0.0 and r > 0.0:
            right_motor.set_speed_backward_0_1(KICK_LEVEL)
            time.sleep_ms(KICK_MS)

        left_motor.set_speed_backward_0_1(l)
        right_motor.set_speed_backward_0_1(r)

    _last_L, _last_R = l, r


def stop_all():
    set_wheel_speeds_forward(0.0, 0.0)
    left_motor.stop()
    right_motor.stop()


def motor_test():
    # Gira cada motor para verificar que sí mueve (independiente de sensores)
    print("Motor test: IZQUIERDO adelante")
    left_motor.set_speed_forward_0_1(0.9 if DRIVE_DIR >= 0 else 0.0)
    right_motor.set_speed_forward_0_1(0.0)
    time.sleep_ms(600)

    print("Motor test: DERECHO adelante")
    left_motor.set_speed_forward_0_1(0.0)
    right_motor.set_speed_forward_0_1(0.9 if DRIVE_DIR >= 0 else 0.0)
    time.sleep_ms(600)

    stop_all()
    time.sleep_ms(200)


# ========= WIFI / API HELPERS =========
def connect_wifi(ssid=WIFI_SSID, password=WIFI_PASS, timeout_s=12):
    if not ssid or not password:
        if DEBUG:
            print("WIFI: credenciales no establecidas. Saltando conexión.")
        return False
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.active():
        sta_if.active(True)
    if sta_if.isconnected():
        if DEBUG:
            print("WIFI: ya conectado:", sta_if.ifconfig())
        return True
    sta_if.connect(ssid, password)
    start = time.time()
    while not sta_if.isconnected() and (time.time() - start) < timeout_s:
        time.sleep_ms(200)
    if sta_if.isconnected():
        if DEBUG:
            print("WIFI conectado:", sta_if.ifconfig())
        return True
    else:
        if DEBUG:
            print("WIFI: no se pudo conectar en el tiempo dado")
        return False


def log_accion(accion, velocidad_izq, velocidad_der):
    """
    Envía POST a API_URL con {instruccion, velocidad}
    velocidad: se guarda como texto "L,R" para preservar ambos valores.
    """
    if not API_URL:
        if DEBUG:
            print("API_URL no configurada, no se envía registro.")
        return
    payload = {
        "instruccion": accion,
        "velocidad": "{:.2f},{:.2f}".format(velocidad_izq, velocidad_der)
    }
    try:
        # urequests puede no soportar json=, por eso usamos ujson y headers
        headers = {'Content-Type': 'application/json'}
        r = requests.post(API_URL, data=ujson.dumps(payload), headers=headers, timeout=API_TIMEOUT_S)
        if DEBUG:
            print("API ->", API_URL, "payload:", payload, "status:", getattr(r, 'status_code', None))
        try:
            r.close()
        except Exception:
            pass
    except Exception as e:
        if DEBUG:
            print("Error enviando a la API:", e)


def setup():
    stop_all()
    time.sleep_ms(150)
    # Intentamos conectar WiFi al iniciar (si credentials están puestas)
    try:
        connect_wifi()
    except Exception as e:
        if DEBUG:
            print("setup: fallo conexión wifi:", e)
    if RUN_MOTOR_TEST_ON_BOOT:
        motor_test()


def startup_until_center_seen():
    """
    Arranque: buscar línea negra hasta que el sensor central la vea.
    Se aplica la regla de apagar lado correspondiente,
    con prioridad a giros asistidos por el sensor central.
    """
    while True:
        blacks, raw = read_sensors_black_stable()
        left_side  = blacks[0] or blacks[1]
        center     = blacks[2]
        right_side = blacks[3] or blacks[4]

        # Intersección (centro + ambos lados): mantener recto
        if center and left_side and right_side:
            accion = "START: intersección (C+L+R) -> recto"
            set_wheel_speeds_forward(BASE_SPEED, BASE_SPEED)
            log_accion(accion, BASE_SPEED, BASE_SPEED)
            if DEBUG:
                print("START: intersección (C+L+R) -> recto", raw, blacks)
            time.sleep_ms(150)
            break

        # Giro asistido por centro
        if center and left_side and not right_side:
            accion = "START: girar izquierda (asistido centro)"
            set_wheel_speeds_forward(0.0, TURN_SPEED)  # gira a la izquierda (apaga motor izq)
            log_accion(accion, 0.0, TURN_SPEED)
        elif center and right_side and not left_side:
            accion = "START: girar derecha (asistido centro)"
            set_wheel_speeds_forward(TURN_SPEED, 0.0)  # gira a la derecha (apaga motor der)
            log_accion(accion, TURN_SPEED, 0.0)
        # Centro solo: recto y salir
        elif center and not left_side and not right_side:
            accion = "START: recto"
            set_wheel_speeds_forward(BASE_SPEED, BASE_SPEED)
            log_accion(accion, BASE_SPEED, BASE_SPEED)
            if DEBUG:
                print("CENTER DETECTED (start). raw:", raw, "black:", blacks)
            time.sleep_ms(150)
            break
        # Reglas base (respaldo)
        elif right_side and not left_side:
            accion = "START: girar derecha (base)"
            set_wheel_speeds_forward(TURN_SPEED, 0.0)
            log_accion(accion, TURN_SPEED, 0.0)
        elif left_side and not right_side:
            accion = "START: girar izquierda (base)"
            set_wheel_speeds_forward(0.0, TURN_SPEED)
            log_accion(accion, 0.0, TURN_SPEED)
        else:
            accion = "START: perdido (cruise)"
            set_wheel_speeds_forward(CRUISE_WHEN_LOST, CRUISE_WHEN_LOST)
            log_accion(accion, CRUISE_WHEN_LOST, CRUISE_WHEN_LOST)

        if DEBUG:
            print("START raw:", raw, "black:", blacks)

        time.sleep_ms(5)


def loop():
    # 1) Arranque: hasta que el central vea negro
    startup_until_center_seen()

    # 2) Seguimiento con giros asistidos por el sensor central
    while True:
        blacks, raw = read_sensors_black_stable()
        left_side  = blacks[0] or blacks[1]
        center     = blacks[2]
        right_side = blacks[3] or blacks[4]

        # Intersección (centro + ambos lados): recto
        if center and left_side and right_side:
            accion = "recto (intersección)"
            L = BASE_SPEED
            R = BASE_SPEED
        # Giros asistidos por centro
        elif center and left_side and not right_side:
            accion = "girar izquierda (asistido centro)"
            L = 0.0
            R = TURN_SPEED
        elif center and right_side and not left_side:
            accion = "girar derecha (asistido centro)"
            L = TURN_SPEED
            R = 0.0
        # Centro solo: recto
        elif center and not left_side and not right_side:
            accion = "recto (solo centro)"
            L = BASE_SPEED
            R = BASE_SPEED
        # Reglas base (respaldo)
        elif right_side and not left_side:
            accion = "girar derecha (base)"
            L = TURN_SPEED
            R = 0.0
        elif left_side and not right_side:
            accion = "girar izquierda (base)"
            L = 0.0
            R = TURN_SPEED
        else:
            accion = "perdido"
            L = CRUISE_WHEN_LOST
            R = CRUISE_WHEN_LOST

        # Registro en API (la API guarda 'velocidad' como texto "L,R")
        log_accion(accion, L, R)

        set_wheel_speeds_forward(L, R)

        if DEBUG:
            print("raw:", raw, "black:", blacks, "L:", round(L, 2), "R:", round(R, 2))

        time.sleep_ms(3)


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        stop_all()