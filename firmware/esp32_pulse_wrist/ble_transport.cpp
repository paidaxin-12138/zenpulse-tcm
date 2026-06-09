#include "ble_transport.h"

#if ENABLE_BLE

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

static const char *kDeviceName = "ZenPulse";
static const char *kServiceUuid = "0000fff0-0000-1000-8000-00805f9b34fb";
static const char *kNotifyUuid = "0000fff1-0000-1000-8000-00805f9b34fb";

static BLEServer *gServer = nullptr;
static BLECharacteristic *gNotifyChar = nullptr;
static bool gConnected = false;

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *) override { gConnected = true; }
  void onDisconnect(BLEServer *) override {
    gConnected = false;
    if (gServer) gServer->startAdvertising();
  }
};

void bleTransportBegin() {
  BLEDevice::init(kDeviceName);
  gServer = BLEDevice::createServer();
  gServer->setCallbacks(new ServerCallbacks());
  BLEService *service = gServer->createService(kServiceUuid);
  gNotifyChar = service->createCharacteristic(
      kNotifyUuid,
      BLECharacteristic::PROPERTY_NOTIFY);
  gNotifyChar->addDescriptor(new BLE2902());
  service->start();
  BLEAdvertising *adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(kServiceUuid);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
  Serial.println("[OK] BLE GATT ZenPulse");
}

void bleTransportEmitSample(long ir1, long ir2) {
  if (!gNotifyChar || !gConnected) return;
  char buf[48];
  snprintf(buf, sizeof(buf), "CH1:%ld,CH2:%ld\n", ir1, ir2);
  gNotifyChar->setValue((uint8_t *)buf, strlen(buf));
  gNotifyChar->notify();
}

void bleTransportPoll() {}

bool bleTransportIsConnected() { return gConnected; }

#else

void bleTransportBegin() {}
void bleTransportEmitSample(long, long) {}
void bleTransportPoll() {}
bool bleTransportIsConnected() { return false; }

#endif
