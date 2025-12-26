#include <WiFi.h>
#include <PubSubClient.h>

WiFiClient net;
PubSubClient client(net);

const char* WIFI_SSID = "acer123";
const char* WIFI_PASS = "acer1234";

const char* BROKER = "broker.hivemq.com";
const int   PORT   = 1883;
const char* topic = "iot/tilapia/data";

void connectWiFi() {
  Serial.print("Connecting WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  Serial.print("Connecting MQTT...");
  while (!client.connect("esp32-tilapia-test")) {
    Serial.print(".");
    delay(500);
  }
  Serial.println(" OK");
}

// Tạo dữ liệu random theo phân phối
float generateData(String scenario) {
  if (scenario == "SAFE") {
    // DO: 6-10, Temp: 28-32, pH: 6.5-8.5
    return random(0, 100);  // Sẽ map theo loại sensor
  } else if (scenario == "WARNING") {
    // DO: 2-6, Temp: 24-28 hoặc 32-35, pH: 6-6.5 hoặc 8.5-9
    return random(0, 100);
  } else {  // DANGER
    // DO: <2, Temp: <24 hoặc >35, pH: <6 hoặc >9
    return random(0, 100);
  }
}

String getTimestamp() {
  // Tạo timestamp giả từ millis
  unsigned long now = millis() / 1000;  // giây
  
  // Giả lập format: 2024-01-01 12:00:00
  int hours = (now / 3600) % 24;
  int minutes = (now / 60) % 60;
  int seconds = now % 60;
  
  char timestamp[20];
  sprintf(timestamp, "2024-11-25 %02d:%02d:%02d", hours, minutes, seconds);
  
  return String(timestamp);
}

void setup() {
  Serial.begin(115200);
  
  // Random seed từ analog pin
  randomSeed(analogRead(0));
  
  connectWiFi();
  client.setServer(BROKER, PORT);
  connectMQTT();
  
  Serial.println("\n🚀 ESP32 Test Mode - Random Data Generator");
  Serial.println("==================================================");
}

void loop() {
  client.loop();

  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!client.connected()) connectMQTT();

  // Chọn scenario random: 40% Safe, 50% Warning, 10% Danger
  int rand_scenario = random(0, 100);
  String scenario;
  
  if (rand_scenario < 10) {
    scenario = "DANGER";
  } else if (rand_scenario < 60) {
    scenario = "WARNING";
  } else {
    scenario = "SAFE";
  }

  // Generate data theo scenario
  float temp, dox, ph, turb;
  
  if (scenario == "SAFE") {
    temp = random(2800, 3200) / 100.0;   // 28-32°C
    dox = random(600, 1000) / 100.0;     // 6-10 mg/L
    ph = random(650, 850) / 100.0;       // 6.5-8.5
    turb = random(500, 2000) / 100.0;    // 5-20 NTU
  } else if (scenario == "WARNING") {
    temp = random(2400, 2800) / 100.0;   // 24-28°C hoặc 32-35
    if (random(0, 2) == 0) {
      temp = random(3200, 3500) / 100.0;
    }
    dox = random(200, 600) / 100.0;      // 2-6 mg/L
    ph = random(600, 650) / 100.0;       // 6-6.5 hoặc 8.5-9
    if (random(0, 2) == 0) {
      ph = random(850, 900) / 100.0;
    }
    turb = random(2000, 3500) / 100.0;   // 20-35 NTU
  } else {  // DANGER
    temp = random(2000, 2400) / 100.0;   // <24°C hoặc >35
    if (random(0, 2) == 0) {
      temp = random(3500, 4000) / 100.0;
    }
    dox = random(40, 200) / 100.0;       // 0.4-2 mg/L
    ph = random(500, 600) / 100.0;       // <6 hoặc >9
    if (random(0, 2) == 0) {
      ph = random(900, 1000) / 100.0;
    }
    turb = random(3500, 4000) / 100.0;   // 35-40 NTU
  }

  String timestamp = getTimestamp();

  // Tạo JSON
  String json = "{";
  json += "\"Temperature\":" + String(temp, 2) + ",";
  json += "\"Dissolved_Oxygen\":" + String(dox, 2) + ",";
  json += "\"pH\":" + String(ph, 2) + ",";
  json += "\"Turbidity\":" + String(turb, 2) + ",";
  json += "\"timestamp\":\"" + timestamp + "\"";
  json += "}";

  // Publish
  if (client.publish(topic, json.c_str())) {
    Serial.print("📤 [" + scenario + "] ");
    Serial.println(json);
  } else {
    Serial.println("❌ Publish failed!");
  }

  delay(3000);  // Gửi mỗi 3 giây
}
