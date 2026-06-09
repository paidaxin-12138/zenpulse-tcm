#pragma once

#include <Arduino.h>

void bleTransportBegin();
void bleTransportEmitSample(long ir1, long ir2);
void bleTransportPoll();
bool bleTransportIsConnected();
