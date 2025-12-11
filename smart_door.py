from flask import Flask, request, jsonify, render_template
import RPi.GPIO as GPIO
import threading
import time
import os
from datetime import datetime

GPIO.setmode(GPIO.BCM)

# ============================================================
# PIN SETUP
# ============================================================
SERVO_PIN = 18
BUZZER_PIN = 25
LED_RED = 23
LED_GREEN = 24

GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)

# ============================================================
# GLOBALS
# ============================================================
current_state = "locked"
wrong_attempts = 0
MAX_ATTEMPTS = 3
timer_active = False
auto_lock_thread = None   # <<< NEW

# ============================================================
# PASSWORD SYSTEM
# ============================================================
PASSWORD_FILE = "/home/pi/SmartDoor/password.txt"

def load_password():
    try:
        with open(PASSWORD_FILE, "r") as f:
            return f.read().strip()
    except:
        return "2025"  # fallback default

def save_password(new_pw):
    with open(PASSWORD_FILE, "w") as f:
        f.write(new_pw)

# ============================================================
# LOGGING SYSTEM
# ============================================================
LOG_DIR = "/home/pi/SmartDoor/logs"
LOG_FILE = f"{LOG_DIR}/events.log"
os.makedirs(LOG_DIR, exist_ok=True)

def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# ============================================================
# SERVO
# ============================================================
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def set_angle(angle):
    duty = angle / 18 + 2
    servo.ChangeDutyCycle(duty)
    time.sleep(0.4)
    servo.ChangeDutyCycle(0)

# ============================================================
# BUZZER (ACTIVE LOW)
# ============================================================
def buzzer_on():
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def buzzer_off():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)

def buzzer_beep(count=2):
    for _ in range(count):
        buzzer_on()
        time.sleep(0.2)
        buzzer_off()
        time.sleep(0.1)

# ============================================================
# ALARM
# ============================================================
def alarm():
    global current_state
    write_log("ALARM TRIGGERED — too many wrong attempts")

    for _ in range(20):
        buzzer_on()
        GPIO.output(LED_RED, GPIO.LOW)
        time.sleep(0.15)
        buzzer_off()
        GPIO.output(LED_RED, GPIO.HIGH)
        time.sleep(0.15)

    lock()
    current_state = "locked"

# ============================================================
# LED CONTROL (COMMON ANODE)
# ============================================================
def red_on():
    GPIO.output(LED_RED, GPIO.LOW)

def red_off():
    GPIO.output(LED_RED, GPIO.HIGH)

def green_on():
    GPIO.output(LED_GREEN, GPIO.LOW)

def green_off():
    GPIO.output(LED_GREEN, GPIO.HIGH)

# ============================================================
# LOCK / UNLOCK
# ============================================================
def lock():
    global current_state
    write_log("DOOR LOCKED")
    set_angle(0)
    red_on()
    green_off()
    current_state = "locked"

def unlock():
    global current_state
    write_log("DOOR UNLOCKED (password correct)")
    set_angle(90)
    red_off()
    green_on()
    current_state = "unlocked"

# ============================================================
# FIXED AUTO-LOCK SYSTEM
# ============================================================
def auto_lock_delay(my_id):
    global timer_active
    time.sleep(30)

    # Ignore old expired threads
    if my_id != auto_lock_thread:
        return

    lock()
    write_log("AUTO-LOCK ACTIVATED (timer expired)")
    timer_active = False

def start_auto_lock():
    global timer_active, auto_lock_thread

    timer_active = True
    auto_lock_thread = object()  # unique ID
    my_id = auto_lock_thread

    threading.Thread(target=auto_lock_delay, args=(my_id,), daemon=True).start()
    print("[SYSTEM] Auto-lock timer restarted.")

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/change_password_page")
def change_password_page():
    return render_template("change_password.html")

# ============================================================
# UNLOCK ROUTE
# ============================================================
@app.route("/unlock", methods=["POST"])
def route_unlock():
    global wrong_attempts

    data = request.get_json()
    password = data.get("password")
    stored_pw = load_password()

    if password == stored_pw:
        wrong_attempts = 0
        unlock()
        start_auto_lock()
        return jsonify({"status": "unlocked"})

    else:
        wrong_attempts += 1
        write_log(f"WRONG PASSWORD ATTEMPT ({wrong_attempts}/{MAX_ATTEMPTS})")

        if wrong_attempts >= MAX_ATTEMPTS:
            wrong_attempts = 0
            threading.Thread(target=alarm, daemon=True).start()
            return jsonify({"status": "alarm"})

        buzzer_beep(3)
        return jsonify({"status": "wrong_password"})

# ============================================================
# MANUAL LOCK
# ============================================================
@app.route("/lock", methods=["POST"])
def route_lock():
    lock()
    return jsonify({"status": "locked"})

# ============================================================
# STATUS
# ============================================================
@app.route("/status")
def get_status():
    return jsonify({"state": current_state})

# ============================================================
# ADMIN LOG VIEW
# ============================================================
@app.route("/admin")
def admin_page():
    try:
        with open(LOG_FILE, "r") as f:
            logs = f.read()
    except:
        logs = "No logs yet."

    return render_template("admin.html", logs=logs)

@app.route("/download_logs")
def download_logs():
    return open(LOG_FILE, "rb").read()

@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    open(LOG_FILE, "w").close()
    write_log("LOGS CLEARED BY ADMIN")
    return jsonify({"status": "cleared"})

# ============================================================
# CHANGE PASSWORD
# ============================================================
@app.route("/change_password", methods=["POST"])
def change_password():
    data = request.get_json()
    old_pw = data.get("old")
    new_pw = data.get("new")

    stored_pw = load_password()

    if old_pw != stored_pw:
        write_log("FAILED PASSWORD CHANGE (wrong current password)")
        return jsonify({"status": "error", "message": "Current password incorrect"})

    save_password(new_pw)
    write_log("PASSWORD CHANGED SUCCESSFULLY")

    return jsonify({"status": "success"})

# ============================================================
# START SERVER
# ============================================================
if __name__ == "__main__":
    try:
        buzzer_off()
        red_on()
        green_off()
        set_angle(0)
        write_log("SYSTEM BOOT — door locked")

        app.run(host="0.0.0.0", port=5000)

    finally:
        servo.stop()
        GPIO.cleanup()
