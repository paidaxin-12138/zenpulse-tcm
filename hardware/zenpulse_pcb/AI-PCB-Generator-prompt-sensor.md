# AI-PCB-Generator — Sensor Board Prompt

> **单独第二个工程**：Main 板完成后，新建项目粘贴下方 Prompt  
> 通过 **8P FPC** 与 Main 板连接，不在 Sensor 板放 ESP32 / 电池

---

## English Prompt（复制从这里开始）

```
Design a 2-layer small sensor PCB for a wearable PPG wristband.

Board constraints:
- Board size: 34mm x 16mm, 0.8mm thickness, 2 copper layers
- Bottom side faces human skin; top side has FPC connector
- Target manufacturer: JLCPCB

Components:
1. Two MAX30102 pulse oximeter ICs (or 14mmx14mm breakout module footprints)
   - U1 MAX30102 #1: I2C address 0x57, ADDR/SADO pin tied to GND
   - U2 MAX30102 #2: I2C address 0xAE, ADDR/SADO pin tied to 3.3V
   - Center-to-center spacing between the two sensors: 12mm along long axis
   - Each MAX30102: 100nF + 1uF decoupling on 3.3V within 2mm of chip

2. FPC connector 0.5mm pitch 8-pin (same series as main board, bottom contact)

Optional (place if space allows):
3. MPU6050 accelerometer, I2C address 0x68, AD0 to GND

Power and I2C from FPC only (no local LDO):
- Pin1 GND
- Pin2 +3V3 input from main board (max 200mA)
- Pin3 I2C_SDA (shared bus)
- Pin4 I2C_SCL (shared bus)
- Pin5 GND
- Pin6 NC
- Pin7 NC
- Pin8 GND

Layout rules:
1. Place both MAX30102 on BOTTOM layer (skin side) with LED/photodiode facing bottom
2. Keep 5.5mm diameter keep-out around each LED on bottom (for mechanical light window in plastic enclosure)
3. FPC connector on TOP layer at board edge opposite from sensors
4. Short wide traces for +3V3 (0.4mm min) because LED pulses draw current
5. I2C traces: 0.2mm, length matched, ground guard if possible
6. NO pull-up resistors on sensor board (pull-ups on main board only)
7. Solid ground pour on bottom layer except LED windows

Do NOT include ESP32, battery, or OLED on this board.

Label nets: +3V3, GND, I2C_SDA, I2C_SCL

Generate schematic, BOM, 2-layer PCB, DRC/DFM, KiCad export.
```

---

## 生成后必改项

- [ ] U1 **ADDR → GND**，U2 **ADDR → 3V3**（用万用表/原理图核对，与固件 0x57/0xAE 一致）
- [ ] 两颗传感器 **间距 12 mm**，LED 朝 **Bottom**
- [ ] FPC Pin 定义与 Main 板 **完全一致**
- [ ] Sensor 板 **无 I2C 上拉电阻**

---

## 首版焊接建议

- 若 AI 选用 QFN 裸 MAX30102：建议改焊 **14×14 模块 footprint**（首版成功率更高）
- 模块第三脚 ADDR：一颗接 GND、一颗接 3V3
