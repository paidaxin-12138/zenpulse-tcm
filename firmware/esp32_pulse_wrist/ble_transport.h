// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

#pragma once

#include <Arduino.h>

void bleTransportBegin();
void bleTransportEmitSample(long ir1, long ir2);
void bleTransportPoll();
bool bleTransportIsConnected();
