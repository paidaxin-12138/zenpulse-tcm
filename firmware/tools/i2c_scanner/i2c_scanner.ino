// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

/**
 * I2C 扫描 — ESP32-S3 默认 GPIO8/9，经典 ESP32 改为 21/22
 */
#include <Wire.h>

#ifndef USE_ESP32_S3
#define USE_ESP32_S3 1
#endif

#if USE_ESP32_S3
#define I2C_SDA 8
#define I2C_SCL 9
#else
#define I2C_SDA 21
#define I2C_SCL 22
#endif

void setup() {
  Serial.begin(115200);
  delay(500);
  Wire.begin(I2C_SDA, I2C_SCL);
  Serial.printf("\nI2C Scanner SDA=%d SCL=%d\n", I2C_SDA, I2C_SCL);
}

void loop() {
  byte count = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("0x%02X\n", addr);
      count++;
    }
    delay(2);
  }
  Serial.printf("Found %u device(s)\n\n", count);
  delay(3000);
}
