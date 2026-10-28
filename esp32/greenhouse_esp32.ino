/*
 * ==============================================================================
 * 🌱 Greenhouse Monitoring System - ESP32 Firmware
 * ==============================================================================
 * Sensors:
 *   - DHT22 / DHT11 : Temperature & Relative Humidity (Digital GPIO 4)
 *   - LDR Sensor    : Light Irradiance (Analog ADC1 GPIO 34)
 *   - MQ-135 Sensor : Air Quality / Hazardous Gas (Analog ADC1 GPIO 35)
 *
 * Transmits telemetry via HTTP POST to the Flask REST backend at:
 *   http://<SERVER_IP>:5000/data
 * ==============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// ==============================================================================
// 1. Configuration & WiFi Credentials
// ==============================================================================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Target Flask Server Endpoint (Replace with your PC's Local IP, e.g., 192.168.1.100)
const char* SERVER_URL    = "http://192.168.1.100:5000/data";

// Telemetry Transmission Interval (milliseconds)
const unsigned long POST_INTERVAL_MS = 3000;  // 3 seconds

// ==============================================================================
// 2. Hardware Pin Definitions
// ==============================================================================
#define DHTPIN        4       // Digital Pin for DHT22/DHT11 Data
#define DHTTYPE       DHT22   // Change to DHT11 if using DHT11
#define PIN_LDR       34      // ADC1 Pin for Light Dependent Resistor (LDR)
#define PIN_MQ135     35      // ADC1 Pin for MQ-135 Gas Sensor
#define PIN_STATUS_LED 2      // Onboard LED for status indication

DHT dht(DHTPIN, DHTTYPE);

unsigned long lastPostTime = 0;


// ==============================================================================
// 3. Helper Functions
// ==============================================================================

void connectToWiFi() {
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    // Blink LED while connecting
    digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(PIN_STATUS_LED, HIGH); // Steady ON when connected
  } else {
    Serial.println("\n[WiFi] Connection timeout. Retrying in loop...");
    digitalWrite(PIN_STATUS_LED, LOW);
  }
}


float readSmoothedADC(int pin, int samples = 10) {
  long total = 0;
  for (int i = 0; i < samples; i++) {
    total += analogRead(pin);
    delay(5);
  }
  return (float)(total / samples);
}


void transmitSensorData(float temperature, float humidity, int light, int gas) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Lost connection. Reconnecting...");
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  // Construct JSON payload
  String payload = "{";
  payload += "\"temperature\":" + String(temperature, 1) + ",";
  payload += "\"humidity\":" + String(humidity, 1) + ",";
  payload += "\"light\":" + String(light) + ",";
  payload += "\"gas\":" + String(gas);
  payload += "}";

  Serial.print("[HTTP] Sending POST: ");
  Serial.println(payload);

  int httpResponseCode = http.POST(payload);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("[HTTP] Server Response (");
    Serial.print(httpResponseCode);
    Serial.print("): ");
    Serial.println(response);

    // Quick flash LED to indicate successful transmission
    digitalWrite(PIN_STATUS_LED, LOW);
    delay(50);
    digitalWrite(PIN_STATUS_LED, HIGH);
  } else {
    Serial.print("[HTTP] Error sending POST request: ");
    Serial.println(httpResponseCode);
    digitalWrite(PIN_STATUS_LED, LOW);
  }

  http.end();
}


// ==============================================================================
// 4. Setup & Loop
// ==============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=================================================");
  Serial.println("🌱 Greenhouse Monitoring System - ESP32 Booting");
  Serial.println("=================================================");

  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_LDR, INPUT);
  pinMode(PIN_MQ135, INPUT);

  // Configure ADC resolution (12-bit: 0 - 4095)
  analogReadResolution(12);

  // Initialize DHT Sensor
  dht.begin();
  Serial.println("[Sensors] DHT Initialized.");

  // Connect to Network
  connectToWiFi();
}


void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastPostTime >= POST_INTERVAL_MS) {
    lastPostTime = currentMillis;

    // 1. Read Environmental Sensors
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature(); // Celsius

    // 2. Read Light and Gas ADC Sensors
    int light = (int)readSmoothedADC(PIN_LDR, 10);
    int gas = (int)readSmoothedADC(PIN_MQ135, 10);

    // Validate DHT sensor readings
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("[Sensor Error] Failed to read from DHT sensor! Retrying...");
      return;
    }

    // Print to Serial Monitor
    Serial.println("----------------------------------------");
    Serial.printf("Temp: %.1f C | Humidity: %.1f %% | Light: %d | Gas: %d\n",
                  temperature, humidity, light, gas);

    // Transmit to Backend
    transmitSensorData(temperature, humidity, light, gas);
  }
}
