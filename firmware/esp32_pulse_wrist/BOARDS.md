# 开发板与引脚（ESP32-S3 / ESP32）

## 推荐：ESP32-S3-DevKitC-1

| 项目 | 说明 |
|------|------|
| 模组 | ESP32-S3-WROOM-1（N16R8 或 N8R2 均可） |
| `config.h` | `#define USE_ESP32_S3 1` |
| I2C SDA | **GPIO 8** |
| I2C SCL | **GPIO 9** |
| 3.3V / GND | 开发板排针 3V3、GND → MAX30102 ×2 |
| USB | 原生 USB（Type-C）；烧录与串口监视器走同一口 |
| PlatformIO | `pio run -e esp32-s3-devkitc-1 -t upload` |

### Arduino IDE 设置（ESP32-S3）

1. 开发板：**ESP32S3 Dev Module**
2. USB CDC On Boot：**Enabled**
3. Flash Size：按模组选 8MB / 16MB
4. PSRAM：N16R8 选 **OPI PSRAM**

### 注意

- **勿** 用 GPIO19/20（USB D-/D+）接 I2C  
- **勿** 用 GPIO26–32（部分模组接 Flash/PSRAM，不可用）  
- 腕带走线尽量短；S3 主频高，I2C 400 kHz 一般稳定  

---

## 备选：ESP32-WROOM-32 DevKit

| 项目 | 说明 |
|------|------|
| `config.h` | `#define USE_ESP32_S3 0` |
| I2C | GPIO **21** (SDA)、**22** (SCL) |
| PlatformIO | `pio run -e esp32dev -t upload` |

---

## 接线表（共用）

| 开发板 | MAX30102 #1 | MAX30102 #2 | MPU6050 |
|--------|-------------|-------------|---------|
| 3.3V | VIN | VIN | VCC |
| GND | GND | GND | GND |
| SDA | SDA | SDA | SDA |
| SCL | SCL | SCL | SCL |

---

## I2C 地址

| 器件 | 地址 |
|------|------|
| MAX30102 #1 | 0x57 |
| MAX30102 #2 | 0xAE（SDO→VCC） |
| MPU6050 | 0x68 |

烧录 `firmware/tools/i2c_scanner/i2c_scanner.ino` 前在文件顶部改 SDA/SCL 与上表一致。
