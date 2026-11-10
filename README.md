# myPatras

Prompt library and design notes.

- [`prompts/tridosha_sensor_circuit_prompt.md`](prompts/tridosha_sensor_circuit_prompt.md) —
  prompt for designing a wearable (watch / HRV) circuit and pipeline that
  estimates Vata / Pitta / Kapha balance.
- [`tools/ble_hrv_logger.py`](tools/ble_hrv_logger.py) — logs HR + RR intervals
  from any watch/strap broadcasting the standard BLE Heart Rate Service, and
  reports whether the device actually sends RR (needed for HRV).
