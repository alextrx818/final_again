import json
import time
import paho.mqtt.client as mqtt

# ─── Configuration ─────────────────────────────────────────────────────────────
USER    = "thenecpt"
SECRET  = "0c55322e8e196d6ef9066fa4252cf386"
BROKER  = "mq.thesports.com"
PORT    = 443  # MQTT over WebSocket + TLS port
TOPIC   = "thesports/football/match/v1"

def on_connect(client, userdata, flags, rc):
    """
    Callback when the client receives a CONNACK response from the server.
    """
    if rc == 0:
        print("Connected to broker. Subscribing to topic:", TOPIC)
        client.subscribe(TOPIC)
    else:
        print(f"Connection failed with result code {rc}")

def on_message(client, userdata, msg):
    """
    Callback when a PUBLISH message is received from the server.
    """
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
    except Exception:
        data = payload
    print(f"Message received on {msg.topic}: {data}")

def on_disconnect(client, userdata, rc):
    """
    Callback when the client disconnects unexpectedly.
    Attempts to reconnect until successful.
    """
    print(f"Disconnected (code {rc}). Reconnecting...")
    while True:
        try:
            client.reconnect()
            print("Reconnected to broker.")
            break
        except Exception as e:
            print("Reconnect failed, retrying in 5s:", e)
            time.sleep(5)

def main():
    # Create client with WebSocket transport
    client = mqtt.Client(transport="websockets")
    client.username_pw_set(USER, SECRET)
    client.tls_set()  # Use default TLS settings

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print(f"Connecting to {BROKER}:{PORT} over WebSocket + TLS...")
    client.connect(BROKER, PORT)

    # Enter network loop and stay connected until interrupted
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting and shutting down...")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
