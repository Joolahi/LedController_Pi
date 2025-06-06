from flask import Flask, request
import RPi.GPIO as GPIO
import threading
import time
import atexit


LED_PIN = 17
BUTTON_PIN = 27
button_alert = False


app = Flask(__name__)


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def cleanup():
    GPIO.cleanup()


atexit.register(cleanup)


def monitor_button():
    global button_alert
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            if not button_alert:
                print("Painiketta painettu!")
            button_alert = True
        time.sleep(0.1)


threading.Thread(target=monitor_button, daemon=True).start()

@app.route("/led", methods=["POST"])
def control_led():
    data = request.get_json()
    state = data.get("state")

    if state == "on":
        GPIO.output(LED_PIN, GPIO.HIGH)
        return {"status": "LED turned on"}, 200
    elif state == "off":
        GPIO.output(LED_PIN, GPIO.LOW)
        return {"status": "LED turned off"}, 200
    else:
        return {"error": "Invalid state. Use 'on' or 'off'."}, 400

@app.route("/button", methods=["GET"])
def button_state():
    global button_alert
    return {"alert": button_alert}


@app.route("/button/ack", methods=["POST"])
def button_ack():
    global button_alert
    button_alert = False
    return {"acknowledged": True}, 200

@app.route("/")
def index():
    return """
        <h1>LED Controller</h1>
        <form method="POST" action="/led" onsubmit="send(event)">
            <button type="button" onclick="toggle('on')">Turn ON</button>
            <button type="button" onclick="toggle('off')">Turn OFF</button>
        </form>
        <div id="status" style="margin-top: 20px; font-weight: bold;">Tila: Tuntematon</div>
        <div id="buttonAlert" style="margin-top: 10px; font-size: 18px; color: white; background: red; display: none; padding: 10px; border-radius: 5px;">
            Painiketta painettu!
            <button onclick="acknowledge()" style="margin-left: 10px;">Kuittaa</button>
        </div>

        <script>
            function toggle(state) {
                fetch('/led', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({state: state})
                }).then(r => r.json()).then(data => {
                    document.getElementById("status").textContent = "Tila: " + (data.status || data.error);
                });
            }

            // Tarkista painiketila säännöllisesti
            setInterval(() => {
                fetch('/button')
                    .then(r => r.json())
                    .then(data => {
                        const el = document.getElementById("buttonAlert");
                        if (data.alert) {
                            el.style.display = "inline-block";
                        }
                    });
            }, 1000); // tarkistaa kerran sekunnissa

            // Tarkista painiketila heti sivun latauksen yhteydessä
            window.onload = () => {
                fetch('/button')
                    .then(r => r.json())
                    .then(data => {
                        const el = document.getElementById("buttonAlert");
                        if (data.alert) {
                            el.style.display = "inline-block";
                        }
                    });
            };

            // Kuittaa painiketila
            function acknowledge() {
                fetch('/button/ack', {
                    method: 'POST'
                }).then(() => {
                    document.getElementById("buttonAlert").style.display = "none";
                });
            }
        </script>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
