# ESP32-S3 腕带固件

推荐 **ESP32-S3-DevKitC-1** + 双 MAX30102。

| 文档 | 说明 |
|------|------|
| [BOARDS.md](./BOARDS.md) | S3 / 经典 ESP32 引脚对照 |
| [../../docs/硬件开发指南.md](../../docs/硬件开发指南.md) | 完整硬件流程 |

## 快速开始

```bash
cp config.example.h config.h
# USE_ESP32_S3 1，填 WiFi，I2C 默认 8/9

# PlatformIO（ESP32-S3）
pio run -e esp32-s3-devkitc-1 -t upload
pio device monitor
```

Arduino IDE：板型 **ESP32S3 Dev Module**，**USB CDC On Boot = Enabled**。

## 与经典 ESP32 差异

| 项目 | ESP32-S3 | ESP32 经典 |
|------|----------|------------|
| I2C | GPIO **8** / **9** | GPIO **21** / **22** |
| 串口 | USB 原生 CDC | 通常 USB-UART 芯片 |
| PlatformIO env | `esp32-s3-devkitc-1` | `esp32dev` |
| `config.h` | `USE_ESP32_S3 1` | `USE_ESP32_S3 0` |

协议、TCP 端口、后端联调方式 **不变**。
