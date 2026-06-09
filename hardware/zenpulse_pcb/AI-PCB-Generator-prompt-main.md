# AI-PCB-Generator — Main Board Prompt

> **用法**：在 AI-PCB-Generator 左栏粘贴下方 **English Prompt** 全文 → 点 Design → 人工 Review → Export KiCad → 再改天线区  
> **单独做一块板**：Sensor 板用 `AI-PCB-Generator-prompt-sensor.md`

---

## English Prompt（复制从这里开始）

```
Design a 4-layer wearable main PCB for a BLE health wristband controller.

Board constraints:
- Board size: 38mm x 28mm, 1.0mm thickness, 4 copper layers
- Application: ESP32-S3 BLE + 0.96 inch I2C OLED + LiPo battery wearable
- Target manufacturer: JLCPCB (minimum trace/space 4mil, min drill 0.2mm)

Main components (use JLCPCB/LCSC available parts):
1. ESP32-S3-WROOM-1-N16R8 module (WiFi/BLE MCU)
2. SSD1306 128x64 OLED module interface: 4-pin header 1.27mm (VCC, GND, SDA, SCL) OR FPC for OLED
3. TP4056 linear charger IC (1A charge, PROG resistor 1k to GND)
4. DW01A battery protection + dual 8205A MOSFETs (or integrated LiPo protection module footprint)
5. 3.3V LDO regulator AP2112K-3.3 or XC6220B332MR, 600mA output
6. JST PH 2.0 2-pin battery connector
7. USB Type-C 6-pin receptacle (5V and GND only, CC pins 5.1k to GND each)
8. Tactile switch 3x4mm (KEY to GND, with 10k pull-down on GPIO)
9. Red LED + 1k resistor (status/charge indicator)
10. FPC connector 0.5mm pitch 8-pin bottom contact (Hirose-style) for sensor flex cable

Power architecture:
- USB 5V -> TP4056 -> LiPo cell (3.7V nominal)
- LiPo -> protection circuit -> system rail
- System rail -> 3.3V LDO -> ESP32-S3, OLED, FPC 3V3 pin

I2C bus (400kHz, shared):
- ESP32-S3 GPIO8 = I2C SDA
- ESP32-S3 GPIO9 = I2C SCL
- Connect to OLED SDA/SCL and FPC pins 3 (SDA) and 4 (SCL)
- Single 2.2k pull-up on SDA and SCL to 3.3V near ESP32 only

FPC 8-pin assignment (label nets clearly):
- Pin1 GND
- Pin2 +3V3 (from LDO, capable of 200mA to remote sensor board)
- Pin3 I2C_SDA
- Pin4 I2C_SCL
- Pin5 GND
- Pin6 NC (reserve INT)
- Pin7 NC (reserve INT)
- Pin8 GND

Critical layout rules (MUST follow):
1. ESP32-S3 module antenna area at board edge facing "outer wrist" direction
2. Keep 15mm clearance zone at antenna side: NO copper pour, NO components, NO battery overlap on top/bottom
3. Place 10uF + 100nF decoupling within 3mm of ESP32 3V3 pins
4. Place LDO and TP4056 away from antenna side
5. Battery connector on opposite side from antenna
6. OLED connector on top area center (27mm x 15mm keep-out for display window in enclosure)
7. FPC connector on short edge toward wrist strap routing direction
8. Do NOT use ESP32 GPIO19, GPIO20 (USB), GPIO26-32 (flash/psram)

Additional GPIO:
- GPIO46 (or any free safe GPIO): tactile switch to GND
- GPIO3: status LED through 1k resistor

Ground:
- Solid ground plane on inner layer 2
- Multiple vias stitching GND around ESP32 and FPC

Output nets to label:
- +3V3, +VBAT, +5V_USB, GND, I2C_SDA, I2C_SCL, KEY, LED_STATUS

Generate complete schematic, BOM, and 4-layer PCB layout with DRC and DFM analysis.
Export KiCad compatible files.
```

---

## 生成后必改项（AI 常漏）

- [ ] ESP32-S3 模组 **天线投影区** 下方 L2/L3 **无铜**（对照 Espressif Hardware Design Guidelines）
- [ ] USB-C **CC1/CC2** 各 5.1k 到 GND（若 AI 未加）
- [ ] TP4056 **PROG** = 1k（约 1A 充电电流）
- [ ] FPC **Pin2 3V3** 走线 ≥ **0.4 mm** 宽度
- [ ] I2C 上拉只在 Main 端一组 2.2k
- [ ] 在 KiCad 中打开导出文件，核对 **GPIO8/9** 是否接到 SDA/SCL

---

## 建议 Manufacturer 设置

- Profile: **JLCPCB**
- Layers: **4**
- Thickness: **1.0 mm**
- Surface: **ENIG**
- Quantity: 5（首版）
