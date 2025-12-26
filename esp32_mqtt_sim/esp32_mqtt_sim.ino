// #include <WiFi.h>
// #include <HTTPClient.h>
// #include <PubSubClient.h>

// // WiFiClient net;
// // MQTTClient client;

// WiFiClient net;
// PubSubClient client(net);

// const char* WIFI_SSID = "A7";
// const char* WIFI_PASS = "12345679";
// // const char* WIFI_SSID = "acer123";
// // const char* WIFI_PASS = "acer1234";

// const char* BROKER = "broker.hivemq.com";
// const int   PORT   = 1883;

// const char* serverIP = "192.168.0.136";   // <--- IP của laptop
// String csv_url;  // Sẽ khởi tạo trong setup()

// const char* topic = "iot/tilapia/data";

// void connectWiFi() {
//   Serial.print("Connecting WiFi...");
//   WiFi.begin(WIFI_SSID, WIFI_PASS);
//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }
//   Serial.println(" OK");
// }

// void connectMQTT() {
//   Serial.print("Connecting MQTT...");
//   while (!client.connect("esp32-tilapia")) {
//     Serial.print(".");
//     delay(500);
//   }
//   Serial.println(" OK");
// }

// void setup() {
//   Serial.begin(115200);
  
//   // Khởi tạo URL
//   csv_url = String("http://") + serverIP + ":8000/test.csv";
  
//   connectWiFi();

//   client.setServer(BROKER, PORT);
//   connectMQTT();
// }

// void loop() {
//   client.loop();

//   if (WiFi.status() != WL_CONNECTED)
//     connectWiFi();

//   Serial.println("[ESP32] Fetching CSV from laptop...");

//   HTTPClient http;
//   http.begin(csv_url);

//   int code = http.GET();
//   if (code != 200) {
//     Serial.println("Failed to load CSV (code: " + String(code) + ")");
//     http.end();
//     delay(3000);
//     return;
//   }

//   WiFiClient* stream = http.getStreamPtr();
  
//   // Bỏ header
//   String header = stream->readStringUntil('\n');
//   Serial.println("Header: " + header);

//   int lineCount = 0;
  
//   // Đọc từng dòng từ stream
//   while (http.connected() || stream->available()) {
//     if (stream->available()) {
//       String line = stream->readStringUntil('\n');
//       line.trim();
      
//       if (line.length() == 0) continue;

//       lineCount++;

//       // Parse CSV: DateTime,Temp,DO,pH,Turbidity,Date,Hour
//       int c1 = line.indexOf(',');
//       int c2 = line.indexOf(',', c1 + 1);
//       int c3 = line.indexOf(',', c2 + 1);
//       int c4 = line.indexOf(',', c3 + 1);
//       int c5 = line.indexOf(',', c4 + 1);

//       if (c1 < 0 || c2 < 0 || c3 < 0 || c4 < 0) {
//         Serial.println("⚠️  Skipping invalid line: " + line);
//         continue;
//       }

//       String datetime   = line.substring(0, c1);
//       String temp       = line.substring(c1 + 1, c2);
//       String doValue    = line.substring(c2 + 1, c3);
//       String phValue    = line.substring(c3 + 1, c4);
//       String turbidity  = line.substring(c4 + 1, c5);

//       // Tạo JSON
//       String json = "{";
//       json += "\"Temperature\":" + temp + ",";
//       json += "\"Dissolved_Oxygen\":" + doValue + ",";
//       json += "\"pH\":" + phValue + ",";
//       json += "\"Turbidity\":" + turbidity + ",";
//       json += "\"timestamp\":\"" + datetime + "\"";
//       json += "}";

//       if (!client.connected()) {
//         connectMQTT();
//       }

//       client.publish(topic, json.c_str());

//       Serial.println("📤 [" + String(lineCount) + "] " + json);

//       delay(3000); // 3 giây mỗi dòng
//     }
//     delay(1);
//   }

//   http.end();
//   Serial.println("✅ CSV sent xong (" + String(lineCount) + " dòng) — chờ rồi lặp lại");
//   delay(5000);

// }
#include <WiFi.h>
#include <HTTPClient.h>
#include <PubSubClient.h>

WiFiClient net;
PubSubClient client(net);

const char* WIFI_SSID = "acer123";  // Hotspot laptop
const char* WIFI_PASS = "acer1234";

const char* BROKER = "broker.hivemq.com";
const int   PORT   = 1883;

const char* serverIP = "192.168.137.1";   // IP laptop trên hotspot
String csv_url;

const char* topic = "iot/tilapia/data";

void connectWiFi() {
  Serial.print("Connecting WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println(" OK");

  // In ra thông tin WiFi
  Serial.println("===== WiFi INFO =====");
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());
  Serial.println("=====================");
}

void connectMQTT() {
  Serial.print("Connecting MQTT...");
  while (!client.connect("esp32-tilapia")) {
    Serial.print(".");
    delay(400);
  }
  Serial.println(" OK");
}

void setup() {
  Serial.begin(115200);

  csv_url = String("http://") + serverIP + ":8000/test.csv";

  connectWiFi();

  // In ra URL đang truy cập
  Serial.println("CSV URL = " + csv_url);

  // Test thử kết nối HTTP (HEAD request)
  HTTPClient test;
  test.begin(csv_url);
  int testCode = test.sendRequest("HEAD");
  Serial.print("Test HTTP connection code = ");
  Serial.println(testCode);
  test.end();

  client.setServer(BROKER, PORT);
  connectMQTT();
}

void loop() {
  client.loop();

  if (WiFi.status() != WL_CONNECTED)
    connectWiFi();

  Serial.println("\n========== NEW REQUEST ==========");
  Serial.print("Time: ");
  Serial.println(millis() / 1000);
  Serial.println("[ESP32] Fetching CSV from laptop...");
  Serial.println("URL: " + csv_url);

  HTTPClient http;
  
  Serial.println("🔌 http.begin()...");
  bool beginOK = http.begin(csv_url);
  Serial.print("Begin result: ");
  Serial.println(beginOK ? "OK" : "FAILED");
  
  if (!beginOK) {
    Serial.println("❌ Cannot initialize HTTP connection!");
    delay(3000);
    return;
  }

  Serial.println("📡 Sending GET request...");
  int code = http.GET();
  Serial.print("HTTP Response Code = ");
  Serial.println(code);

  if (code == -1) {
    Serial.println("❌ Connection failed (code -1)");
    Serial.println("💡 Possible causes:");
    Serial.println("   - Firewall blocking port 8000");
    Serial.println("   - Server not running");
    Serial.println("   - Wrong IP address");
    Serial.println("   - AP isolation enabled");
    http.end();
    delay(3000);
    return;
  }

  if (code != 200) {
    Serial.println("❌ Failed to load CSV (code: " + String(code) + ")");
    http.end();
    delay(3000);
    return;
  }

  Serial.println("✅ HTTP 200 OK - Receiving data...");
  WiFiClient* stream = http.getStreamPtr();
  
  // Read header
  String header = stream->readStringUntil('\n');
  Serial.println("Header: " + header);

  int lineCount = 0;

  while (http.connected() || stream->available()) {
    if (stream->available()) {
      String line = stream->readStringUntil('\n');
      line.trim();
      if (line.length() == 0) continue;

      lineCount++;

      int c1 = line.indexOf(',');
      int c2 = line.indexOf(',', c1 + 1);
      int c3 = line.indexOf(',', c2 + 1);
      int c4 = line.indexOf(',', c3 + 1);
      int c5 = line.indexOf(',', c4 + 1);

      if (c1 < 0 || c2 < 0 || c3 < 0 || c4 < 0) {
        Serial.println("⚠️ Skipping invalid line: " + line);
        continue;
      }

      String datetime   = line.substring(0, c1);
      String temp       = line.substring(c1 + 1, c2);
      String doValue    = line.substring(c2 + 1, c3);
      String phValue    = line.substring(c3 + 1, c4);
      String turbidity  = line.substring(c4 + 1, c5);

      // JSON
      String json = "{";
      json += "\"Temperature\":" + temp + ",";
      json += "\"Dissolved_Oxygen\":" + doValue + ",";
      json += "\"pH\":" + phValue + ",";
      json += "\"Turbidity\":" + turbidity + ",";
      json += "\"timestamp\":\"" + datetime + "\"";
      json += "}";

      if (!client.connected())
        connectMQTT();

      client.publish(topic, json.c_str());

      Serial.println("📤 [" + String(lineCount) + "] " + json);

      delay(3000);
    }
    delay(1);
  }

  http.end();
  Serial.println("✅ CSV sent (" + String(lineCount) + " lines)");
  delay(3000);
}
