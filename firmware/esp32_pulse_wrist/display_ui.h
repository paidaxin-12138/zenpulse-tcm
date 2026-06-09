// Copyright (c) 2026 paidaxin-12138
// Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
// https://creativecommons.org/licenses/by-nc/4.0/

#pragma once

#include <Arduino.h>

void displayBegin();
void displayUpdate(long ir1, long ir2, bool bleConnected, bool signalOk);
