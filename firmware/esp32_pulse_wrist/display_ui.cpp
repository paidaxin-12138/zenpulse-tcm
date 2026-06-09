#include "display_ui.h"

#if ENABLE_OLED

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

#ifndef OLED_I2C_ADDR
#define OLED_I2C_ADDR 0x3C
#endif

#ifndef OLED_WIDTH
#define OLED_WIDTH 128
#endif

#ifndef OLED_HEIGHT
#define OLED_HEIGHT 64
#endif

static Adafruit_SSD1306 gDisplay(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
static bool gDisplayOk = false;

// 轻量 HR 估计：3s 环形缓冲 + 峰值计数
static constexpr uint16_t kHrBufLen = 300;
static long gHrBuf[kHrBufLen];
static uint16_t gHrIdx = 0;
static bool gHrBufFull = false;
static float gDisplayHr = 0.0f;
static uint32_t gLastHrCalcMs = 0;

static void calcHrEstimate() {
  uint16_t n = gHrBufFull ? kHrBufLen : gHrIdx;
  if (n < 150) return;

  long sum = 0;
  for (uint16_t i = 0; i < n; i++) sum += gHrBuf[i];
  float mean = (float)sum / n;

  long sq = 0;
  for (uint16_t i = 0; i < n; i++) {
    long d = gHrBuf[i] - (long)mean;
    sq += d * d;
  }
  float stddev = sqrtf((float)sq / n);
  float threshold = mean + stddev * 0.55f;

  uint16_t peaks = 0;
  for (uint16_t i = 1; i + 1 < n; i++) {
    if (gHrBuf[i] > threshold && gHrBuf[i] > gHrBuf[i - 1] && gHrBuf[i] > gHrBuf[i + 1]) {
      peaks++;
    }
  }
  if (peaks >= 2) {
    float durationSec = n / (float)SAMPLE_HZ;
    gDisplayHr = (peaks - 1) * 60.0f / durationSec;
    if (gDisplayHr < 40.0f) gDisplayHr = 40.0f;
    if (gDisplayHr > 180.0f) gDisplayHr = 180.0f;
  }
}

void displayBegin() {
  if (!gDisplay.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR)) {
    Serial.println("[WARN] OLED SSD1306 未检测到 (0x3C)");
    gDisplayOk = false;
    return;
  }
  gDisplayOk = true;
  gDisplay.clearDisplay();
  gDisplay.setTextColor(SSD1306_WHITE);
  gDisplay.setTextSize(1);
  gDisplay.setCursor(0, 0);
  gDisplay.println("ZenPulse");
  gDisplay.println("OLED OK");
  gDisplay.display();
  Serial.println("[OK] OLED SSD1306");
}

void displayUpdate(long ir1, long ir2, bool bleConnected, bool signalOk) {
  if (!gDisplayOk) return;

  gHrBuf[gHrIdx++] = (ir1 + ir2) / 2;
  if (gHrIdx >= kHrBufLen) {
    gHrIdx = 0;
    gHrBufFull = true;
  }

  uint32_t now = millis();
  if (now - gLastHrCalcMs >= 2000) {
    gLastHrCalcMs = now;
    calcHrEstimate();
  }

  gDisplay.clearDisplay();
  gDisplay.setTextSize(1);
  gDisplay.setCursor(0, 0);
  gDisplay.println("ZenPulse Wrist");

  gDisplay.setCursor(0, 12);
  gDisplay.print("BLE: ");
  gDisplay.println(bleConnected ? "Connected" : "Advertising");

  gDisplay.setCursor(0, 24);
  gDisplay.print("Sig: ");
  gDisplay.println(signalOk ? "OK" : "Check fit");

  gDisplay.setTextSize(2);
  gDisplay.setCursor(0, 38);
  if (gDisplayHr > 0) {
    gDisplay.print((int)gDisplayHr);
    gDisplay.setTextSize(1);
    gDisplay.print(" bpm");
  } else {
    gDisplay.setTextSize(1);
    gDisplay.print("HR --");
  }

  gDisplay.setTextSize(1);
  gDisplay.setCursor(0, 56);
  gDisplay.print("IR ");
  gDisplay.print(ir1);
  gDisplay.print("/");
  gDisplay.print(ir2);

  gDisplay.display();
}

#else

void displayBegin() {}
void displayUpdate(long, long, bool, bool) {}

#endif
