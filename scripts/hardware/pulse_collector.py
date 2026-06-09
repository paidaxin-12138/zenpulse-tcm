# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
"""
从 ESP32 腕带 TCP 流采集 PPG，保存 CSV，可选调用 /api/pulse/analyze。

示例:
  python3 scripts/hardware/pulse_collector.py --host 192.168.1.50 --duration 30 --analyze
"""
from __future__ import annotations

import argparse
import csv
import json
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_line(line: str) -> Optional[Dict[str, float]]:
    line = line.strip()
    if not line:
        return None
    parts: Dict[str, float] = {}
    for segment in line.split(","):
        if ":" not in segment:
            continue
        key, val = segment.split(":", 1)
        try:
            parts[key.strip().upper()] = float(val.strip())
        except ValueError:
            continue
    if "CH1" not in parts:
        return None
    return parts


def collect_stream(
    host: str,
    port: int,
    duration_sec: float,
    send_ping: bool = True,
) -> Tuple[List[Dict[str, Any]], List[float]]:
    rows: List[Dict[str, Any]] = []
    merged: List[float] = []
    deadline = time.time() + duration_sec

    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(1.0)
        if send_ping:
            sock.sendall(b"PING\n")
            try:
                sock.recv(64)
            except socket.timeout:
                pass

        while time.time() < deadline:
            try:
                chunk = sock.recv(4096).decode("utf-8", errors="ignore")
            except socket.timeout:
                continue
            if not chunk:
                break
            for line in chunk.splitlines():
                parsed = parse_line(line)
                if not parsed:
                    continue
                ch1 = parsed.get("CH1", 0)
                ch2 = parsed.get("CH2", ch1)
                merged.append((ch1 + ch2) / 2.0)
                rows.append(
                    {
                        "ts_ms": parsed.get("TS"),
                        "ch1": ch1,
                        "ch2": ch2,
                        "ax": parsed.get("AX"),
                        "ay": parsed.get("AY"),
                        "az": parsed.get("AZ"),
                    }
                )

    return rows, merged


def save_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["ts_ms", "ch1", "ch2", "ax", "ay", "az"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def analyze_samples(samples: List[float], api_url: str, fs: float) -> Dict[str, Any]:
    import urllib.error
    import urllib.request

    payload = json.dumps(
        {
            "samples": samples,
            "fs": fs,
            "source": "esp32_wrist",
            "capability_level": "L1",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"API {exc.code}: {body}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="ZenPulse 腕带 TCP 采集")
    parser.add_argument("--host", required=True, help="ESP32 IP")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--duration", type=float, default=30.0, help="采集秒数")
    parser.add_argument("--fs", type=float, default=100.0)
    parser.add_argument("--out", type=Path, default=Path("data/pulse_capture.csv"))
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="采集后 POST /api/pulse/analyze",
    )
    parser.add_argument(
        "--api",
        default="http://127.0.0.1:8000/api/pulse/analyze",
        help="脉象分析 API",
    )
    args = parser.parse_args()

    print(f"连接 {args.host}:{args.port}，采集 {args.duration}s …")
    rows, merged = collect_stream(args.host, args.port, args.duration)
    print(f"收到 {len(rows)} 点")

    if not merged:
        print("未收到数据：请先 nc 测试 TCP，并确认客户端连接后设备才推流", file=sys.stderr)
        return 1

    save_csv(rows, args.out)
    print(f"已保存 {args.out}")

    if args.analyze:
        result = analyze_samples(merged, args.api, args.fs)
        print(json.dumps(
            {
                "pulse_type": result.get("pulse_type"),
                "heart_rate": (result.get("waveform_stats") or {}).get("heart_rate"),
                "valid_beat_count": (result.get("quality") or {}).get("valid_beat_count"),
                "confidence": result.get("confidence"),
            },
            ensure_ascii=False,
            indent=2,
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
