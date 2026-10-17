# IoT-Based Smart Dynamic EV Charging Road

A mini project that demonstrates **dynamic (in-motion) wireless charging** of an electric vehicle prototype using magnetic induction, with **real-time power monitoring over IoT**. A primary coil beneath the "road" transmits energy to a secondary coil on a moving vehicle, and an ESP32 reads the received voltage, current and power and publishes them to a cloud dashboard.

> B.E. Information Technology, IoE Lab Mini Project, University of Mumbai (2026-27)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Hardware Required](#hardware-required)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Wiring](#wiring)
- [Software Setup](#software-setup)
- [Example Firmware](#example-firmware)
- [Results](#results)
- [Applications](#applications)
- [Future Scope](#future-scope)
- [Project Team](#project-team)
- [License](#license)

---

## Overview

Plug-in charging forces an EV to stop, and it contributes to long charging downtime, range anxiety and dependence on fixed charging stations. This project explores a contact-free alternative: charging the vehicle while it moves over an energized road section.

The prototype combines:

- **Inductive power transfer** from a road-side primary coil (Tx) to a vehicle-side secondary coil (Rx)
- **Power conditioning** with a full-wave bridge rectifier and smoothing capacitor
- **Sensing** with an INA219 voltage/current sensor
- **IoT telemetry** with an ESP32 over Wi-Fi / MQTT to an Internet of Energy (IoE) dashboard

## Features

- Wireless, cable-free energy transfer to a moving vehicle prototype
- Real-time measurement of bus voltage, current and power
- Live telemetry to a cloud dashboard over Wi-Fi using MQTT
- Visual confirmation of power transfer through an LED load (the LED is brightest when the coils are well aligned)
- Low-cost, easily available components

## Hardware Required

| Component | Purpose |
|---|---|
| ESP32 microcontroller | Reads sensor data and sends it to the cloud over Wi-Fi |
| INA219 current/voltage sensor | Measures DC voltage and current drawn by the load (up to 26 V, 3.2 A) |
| Primary coil (Tx), enameled copper wire | Road-side transmitting coil |
| Secondary coil (Rx), enameled copper wire | Vehicle-side receiving coil |
| High-frequency oscillator + DC power supply | Drives the primary coil with a high-frequency signal |
| DB107 bridge rectifier | Converts induced AC to DC |
| 100 µF smoothing capacitor | Removes voltage ripple from the rectified output |
| LED + 220 Ω resistor | Simulated EV load |
| Jumper wires, breadboard | Connections |

**Software:** Arduino IDE (C++), an MQTT broker/IoT dashboard of your choice.

## System Architecture

The system is organised into five layers:

1. **Power transmission (road infrastructure):** DC power supply, then high-frequency oscillator, then primary coil, which transfers energy by magnetic induction.
2. **Power reception and conversion (moving EV):** secondary Rx coil, then DB107 bridge rectifier, then 100 µF smoothing capacitor.
3. **Sensing and load:** INA219 power sensor, then the simulated EV load (LED + resistor).
4. **Edge processing:** ESP32 reads the INA219 over the I2C bus (SDA/SCL).
5. **IoE cloud:** ESP32 publishes the data over Wi-Fi / MQTT to an IoT dashboard for real-time monitoring.

```
DC Supply -> HF Oscillator -> Primary Coil ~~(magnetic induction)~~> Secondary Coil
                                                                          |
                                                          Bridge Rectifier + Capacitor
                                                                          |
                                                              INA219 -> LED + Resistor
                                                                |
                                                          (I2C: SDA/SCL)
