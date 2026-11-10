#!/usr/bin/env python3
"""Log RR intervals from any BLE device exposing the standard Heart Rate Service.

Works with watches/straps that broadcast HR over Bluetooth LE (service 0x180D,
characteristic 0x2A37). RR intervals are only present if the device sends them
(flag bit 4) -- many wrist watches send HR only. Run with --scan first.

    pip install bleak
    python ble_hrv_logger.py --scan
    python ble_hrv_logger.py --address AA:BB:CC:DD:EE:FF --seconds 300 --out rr.csv
"""
import argparse
import asyncio
import csv
import math
import time

HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"


def parse_hr_measurement(data: bytes):
    """Parse a Heart Rate Measurement (0x2A37) packet.

    Returns (hr_bpm, contact, rr_ms_list). contact is None if not supported.
    """
    flags = data[0]
    i = 1
    if flags & 0x01:  # HR value is uint16
        hr = int.from_bytes(data[i:i + 2], "little")
        i += 2
    else:
        hr = data[i]
        i += 1
    contact = bool(flags & 0x02) if flags & 0x04 else None
    if flags & 0x08:  # energy expended present
        i += 2
    rr_ms = []
    if flags & 0x10:  # RR intervals present, units of 1/1024 s
        while i + 1 < len(data):
            rr_ms.append(int.from_bytes(data[i:i + 2], "little") * 1000.0 / 1024.0)
            i += 2
    return hr, contact, rr_ms


def rmssd(rr_ms):
    if len(rr_ms) < 3:
        return float("nan")
    d = [b - a for a, b in zip(rr_ms, rr_ms[1:])]
    return math.sqrt(sum(x * x for x in d) / len(d))


async def scan():
    from bleak import BleakScanner
    devices = await BleakScanner.discover(timeout=8.0, return_adv=True)
    for dev, adv in devices.values():
        has_hrs = HR_SERVICE_UUID in [u.lower() for u in adv.service_uuids]
        print(f"{dev.address}  {adv.rssi:4d} dBm  {'[HRS]' if has_hrs else '     '}  {dev.name}")


async def log(address, seconds, out_path):
    from bleak import BleakClient
    rr_all = []
    saw_rr = False
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_host_s", "hr_bpm", "contact", "rr_ms"])

        def on_notify(_, data: bytearray):
            nonlocal saw_rr
            hr, contact, rr = parse_hr_measurement(bytes(data))
            t = time.time()
            if rr:
                saw_rr = True
                for x in rr:
                    w.writerow([f"{t:.3f}", hr, contact, f"{x:.1f}"])
                rr_all.extend(rr)
            else:
                w.writerow([f"{t:.3f}", hr, contact, ""])
            print(f"HR {hr:3d}  RR {[round(x) for x in rr]}  RMSSD(running) {rmssd(rr_all):.1f} ms")

        async with BleakClient(address) as client:
            await client.start_notify(HR_MEASUREMENT_UUID, on_notify)
            await asyncio.sleep(seconds)
            await client.stop_notify(HR_MEASUREMENT_UUID)

    if not saw_rr:
        print("\nDevice sent HR only, no RR intervals -> not usable for HRV via BLE. "
              "Use the vendor SDK/export path instead.")
    else:
        print(f"\n{len(rr_all)} RR intervals, RMSSD {rmssd(rr_all):.1f} ms -> {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scan", action="store_true", help="list nearby BLE devices")
    ap.add_argument("--address", help="device MAC (Linux/Windows) or UUID (macOS)")
    ap.add_argument("--seconds", type=int, default=300)
    ap.add_argument("--out", default="rr.csv")
    a = ap.parse_args()
    if a.scan:
        asyncio.run(scan())
    elif a.address:
        asyncio.run(log(a.address, a.seconds, a.out))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
