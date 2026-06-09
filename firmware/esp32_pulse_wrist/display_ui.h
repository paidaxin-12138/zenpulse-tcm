#pragma once

#include <Arduino.h>

void displayBegin();
void displayUpdate(long ir1, long ir2, bool bleConnected, bool signalOk);
