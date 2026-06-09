#pragma once

// 复制本文件为 config.h 并填写实际值（config.h 勿提交仓库）

#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASSWORD "your-wifi-password"

#define TCP_PORT 8080

// ── 开发板选择（烧录前改 1 处）────────────────────────────
// ESP32-S3 DevKitC-1（推荐，N16R8 / N8R2 等）
#define USE_ESP32_S3 1

// 经典 ESP32-WROOM-32 DevKit（若用旧板改 USE_ESP32_S3 为 0）
// #define USE_ESP32_S3 0

#if USE_ESP32_S3
// ESP32-S3-DevKitC-1 常用 I2C（与 Espressif Arduino 默认一致）
#define I2C_SDA 8
#define I2C_SCL 9
#else
#define I2C_SDA 21
#define I2C_SCL 22
#endif

// MAX30102：第二颗须改 SDO 焊盘
#define MAX30102_ADDR_1 0x57
#define MAX30102_ADDR_2 0xAE

#define SAMPLE_HZ 100

#define MAX30102_LED_BRIGHTNESS 0x24
#define MAX30102_SAMPLE_AVERAGE 4
#define MAX30102_PULSE_WIDTH_US 411

#define ENABLE_IMU 0
#define ENABLE_BLE 1
#define ENABLE_OLED 1
#define OLED_I2C_ADDR 0x3C
#define BACKEND_URL ""
#define MPU6050_ADDR 0x68
