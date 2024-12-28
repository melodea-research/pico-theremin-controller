# MIDI Theremin

## Theory of operation

Converts VL53L1X time-of-flight distance sensor readings into MIDI Control Change messages. Perfect for creating interactive MIDI controllers, gesture-based music interfaces, or experimental instruments.

By positioning the two ToF sensors as the Theremin's antennas, you can create a controller perfect for complimentary parameters such as Frequency and Resonance of a Lowpass Filter.

## Features

- Support for multiple VL53L1X distance sensors
- Real-time distance to MIDI CC conversion
- Value filtering for stable readings
- Automatic sensor address management
- Configurable distance range (10mm - 300mm by default)
- Value change detection to minimize MIDI traffic

## Hardware Requirements

- Any CircuitPython compatible board (tested with Raspberry Pi Pico)
- One or more VL53L1X Time-of-Flight distance sensors

## Pin Connections

Default configuration:
- SDA: GP4
- SCL: GP5
- XSHUT1: GP2
- XSHUT2: GP3

## Software Dependencies

Required CircuitPython libraries:
- `adafruit_vl53l1x`
- `adafruit_midi`
- `busio`
- `usb_midi`

## Installation

1. Install CircuitPython on your board
1. Copy the required libraries to the `lib` folder on your CircuitPython device or use `circup`
1. Connect your distance sensors following the pin configuration
1. Copy `code.py` to your CircuitPython device

## Usage

The device will appear as a USB MIDI device when connected to your computer. Each sensor sends MIDI CC messages on different control numbers:
- Sensor 1: CC 20
- Sensor 2: CC 21
(and so on...)

The distance values are mapped as follows:
- Minimum distance (10mm) = MIDI value 0
- Maximum distance (300mm) = MIDI value 127

## Configuration

You can modify these parameters in the code:
- `MIN_DISTANCE` and `MAX_DISTANCE` in the `DistanceSensor` class
- `ALPHA` value in `ValueFilter` class for smoothing (default: 0.3)
- MIDI CC numbers in `SensorArray.update()`
- I2C and XSHUT pins in `SensorArray.__init__()`

## Class Structure

- `ValueFilter`: Implements Exponential Moving Average Filtering
- `MIDIController`: Handles MIDI communication
- `DistanceSensor`: Manages individual sensor operations
- `SensorArray`: Coordinates multiple sensors and MIDI output

## Troubleshooting I2C errors:
  - Verify wire connections
  - Check for address conflicts
  - Ensure proper power supply

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is released under the MIT License. See LICENSE file for details.
