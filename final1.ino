#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "redmi";             // Your WiFi SSID
const char* password = "12345679";      // Your WiFi Password

const int irSensorPin = D1;             // IR sensor connected to D1 (GPIO5)
const int reedSwitchPin = D2;           // Reed switch connected to D2 (GPIO4)

String serverName = "http://192.168.167.136:5000/alert"; // Flask server on your PC
WiFiClient wifiClient;

void setup() {
  Serial.begin(115200);
  pinMode(irSensorPin, INPUT);
  pinMode(reedSwitchPin, INPUT_PULLUP);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void sendTelegramMessage(String message) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(wifiClient, serverName); // Corrected usage
    http.setTimeout(10000);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{\"message\": \"" + message + "\"}";
    Serial.print("Sending payload: ");
    Serial.println(jsonPayload);

    int httpResponseCode = http.POST(jsonPayload);

    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Server response:");
      Serial.println(response);
    } else {
      Serial.println("❌ Failed to send request.");
    }
    

    http.end();
  } else {
    Serial.println("❌ WiFi not connected");
  }
}

void loop() {
  int irState = digitalRead(irSensorPin);
  int reedState = digitalRead(reedSwitchPin);

  if (irState == LOW && reedState == LOW) {
    Serial.println("Intrusion Detected! Sending alert...");
    sendTelegramMessage("⚠️ Intrusion Detected: Motion + Door/Window opened!");
    delay(5000); // cooldown
  }

  delay(100);
}
