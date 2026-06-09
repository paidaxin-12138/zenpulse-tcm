/**
 * ZenPulse 腕带 — ESP32-S3 / ESP32 + 双 MAX30102 [+ MPU6050]
 *
 * 推荐板：ESP32-S3-DevKitC-1（config.h → USE_ESP32_S3=1，I2C: GPIO8/9）
 * 经典 ESP32：USE_ESP32_S3=0，I2C: GPIO21/22
 *
 * ESP32-S3 串口：Arduino 需启用 USB CDC On Boot，或 PlatformIO 已设 ARDUINO_USB_CDC_ON_BOOT=1
 */

#include <WiFi.h>
#include <Wire.h>
#include "MAX30105.h"
#include "ble_transport.h"
#include "display_ui.h"

#if __has_include("config.h")
#include "config.h"
#else
#error "请先复制 config.example.h 为 config.h"
#endif

#ifndef ENABLE_IMU
#define ENABLE_IMU 0
#endif

#ifndef ENABLE_BLE
#define ENABLE_BLE 0
#endif

#ifndef ENABLE_OLED
#define ENABLE_OLED 0
#endif

MAX30105 sensor1;
MAX30105 sensor2;

WiFiServer server(TCP_PORT);
WiFiClient client;

static uint32_t lastSampleMs = 0;
static uint32_t lastDisplayMs = 0;
static const uint32_t sampleIntervalMs = 1000 / SAMPLE_HZ;
static bool streamEnabled = true;
static uint32_t captureUntilMs = 0;

#if ENABLE_IMU
static bool imuOk = false;

static void mpu6050Init() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  imuOk = Wire.endTransmission() == 0;
  if (imuOk) Serial.println("[OK] MPU6050");
  else Serial.println("[WARN] MPU6050 未检测到");
}

static void mpu6050Read(int16_t &ax, int16_t &ay, int16_t &az) {
  ax = ay = az = 0;
  if (!imuOk) return;
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return;
  if (Wire.requestFrom(MPU6050_ADDR, (uint8_t)6) != 6) return;
  ax = (Wire.read() << 8) | Wire.read();
  ay = (Wire.read() << 8) | Wire.read();
  az = (Wire.read() << 8) | Wire.read();
}
#endif

static bool beginSensor(MAX30105 &sensor, byte address, const char *label) {
  if (!sensor.begin(Wire, I2C_SPEED_FAST, address)) {
    Serial.printf("[ERR] %s (0x%02X)\n", label, address);
    return false;
  }
  sensor.setup(
      MAX30102_LED_BRIGHTNESS,
      MAX30102_SAMPLE_AVERAGE,
      2,
      MAX30102_PULSE_WIDTH_US,
      4096,
      4096);
  sensor.setPulseAmplitudeRed(MAX30102_LED_BRIGHTNESS);
  sensor.setPulseAmplitudeIR(MAX30102_LED_BRIGHTNESS);
  sensor.clearFIFO();
  Serial.printf("[OK] %s @ 0x%02X\n", label, address);
  return true;
}

static void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("WiFi -> %s", WIFI_SSID);
  for (uint8_t i = 0; i < 60 && WiFi.status() != WL_CONNECTED; i++) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[ERR] WiFi 失败，重启");
    delay(3000);
    ESP.restart();
  }
  Serial.print("[OK] IP: ");
  Serial.println(WiFi.localIP());
}

static void handleCommand(const String &line) {
  String cmd = line;
  cmd.trim();
  cmd.toUpperCase();
  if (cmd == "PING") {
    if (client && client.connected()) client.println("PONG");
    return;
  }
  if (cmd == "STREAM") {
    streamEnabled = true;
    captureUntilMs = 0;
    if (client && client.connected()) client.println("OK STREAM");
    return;
  }
  if (cmd.startsWith("CAPTURE")) {
    int sec = cmd.substring(7).toInt();
    if (sec < 1) sec = 20;
    streamEnabled = true;
    captureUntilMs = millis() + (uint32_t)sec * 1000UL;
    if (client && client.connected()) {
      client.printf("OK CAPTURE %d\n", sec);
    }
    return;
  }
}

static void pollCommands() {
  if (!client || !client.connected()) return;
  while (client.available()) {
    String line = client.readStringUntil('\n');
    if (line.length()) handleCommand(line);
  }
}

static void acceptClient() {
  if (client && client.connected()) return;
  if (client) client.stop();
  client = server.available();
  if (client) {
    Serial.println("[TCP] 客户端已连接");
    streamEnabled = true;
  }
}

static void emitSample() {
  long ir1 = sensor1.getIR();
  long ir2 = sensor2.getIR();

#if ENABLE_BLE
  bleTransportEmitSample(ir1, ir2);
#endif

  if (!client || !client.connected()) return;
  if (!streamEnabled) return;
  if (captureUntilMs > 0 && millis() > captureUntilMs) {
    streamEnabled = false;
    client.println("CAPTURE DONE");
    return;
  }

#if ENABLE_IMU
  int16_t ax, ay, az;
  mpu6050Read(ax, ay, az);
  client.printf("TS:%lu,CH1:%ld,CH2:%ld,AX:%d,AY:%d,AZ:%d\n",
                millis(), ir1, ir2, ax, ay, az);
#else
  client.printf("CH1:%ld,CH2:%ld\n", ir1, ir2);
#endif
}

void setup() {
  Serial.begin(115200);
  delay(300);
#if USE_ESP32_S3
  Serial.println("\n=== ZenPulse Wrist HW v1.1 (ESP32-S3) ===");
#else
  Serial.println("\n=== ZenPulse Wrist HW v1.1 (ESP32) ===");
#endif

  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(400000);

  bool ok1 = beginSensor(sensor1, MAX30102_ADDR_1, "PPG #1");
  bool ok2 = beginSensor(sensor2, MAX30102_ADDR_2, "PPG #2");
  if (!ok1 && !ok2) {
    while (true) delay(1000);
  }

#if ENABLE_IMU
  mpu6050Init();
#endif

#if ENABLE_BLE
  bleTransportBegin();
#endif
#if ENABLE_OLED
  displayBegin();
#endif
  connectWiFi();
  server.begin();
  Serial.printf("[OK] TCP:%d BLE:%d OLED:%d IMU:%d\n", TCP_PORT, ENABLE_BLE, ENABLE_OLED, ENABLE_IMU);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  acceptClient();
  pollCommands();

  uint32_t now = millis();
  if (now - lastSampleMs >= sampleIntervalMs) {
    lastSampleMs = now;
    emitSample();
    static uint16_t dbg = 0;
    if (++dbg >= SAMPLE_HZ) {
      dbg = 0;
      Serial.printf("IR1=%ld IR2=%ld\n", sensor1.getIR(), sensor2.getIR());
    }
  }

#if ENABLE_OLED
  if (now - lastDisplayMs >= 250) {
    lastDisplayMs = now;
    long ir1 = sensor1.getIR();
    long ir2 = sensor2.getIR();
    bool sigOk = ir1 > 50000 && ir2 > 50000 && ir1 < 260000 && ir2 < 260000;
    displayUpdate(ir1, ir2, bleTransportIsConnected(), sigOk);
  }
#endif
}
