import usb_midi
import board
import time
import busio
import digitalio
import adafruit_midi
import adafruit_vl53l1x
from adafruit_midi.control_change import ControlChange

# MIDI Configuration
MIDI_CC_1 = 20
MIDI_CC_2 = 22
ALPHA = 0.3

midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    in_channel=0,
    midi_out=usb_midi.ports[1],
    out_channel=0
)

# I2C Setup
SDA = board.GP4
SCL = board.GP5
i2c = busio.I2C(SCL, SDA)

# Wait for I2C bus to be ready
while not i2c.try_lock():
    pass
try:
    print("Initial I2C scan:", [hex(x) for x in i2c.scan()])
finally:
    i2c.unlock()

# Initialize shutdown pins
xshut = [
    digitalio.DigitalInOut(board.GP2),
    digitalio.DigitalInOut(board.GP3),
]

# First, ensure all sensors are shut down
for pin in xshut:
    pin.switch_to_output(value=False)
time.sleep(0.5)  # Wait for shutdown

vl53l1x_sensors = []

# Initialize sensors one at a time
for pin_number, shutdown_pin in enumerate(xshut):
    print(f"Initializing sensor {pin_number + 1}")
    
    # Power up this sensor
    shutdown_pin.value = True
    time.sleep(0.5)  # Give sensor time to wake up
    
    # Scan I2C bus to verify sensor is visible
    while not i2c.try_lock():
        pass
    try:
        devices = i2c.scan()
        print(f"I2C devices found after enabling sensor {pin_number + 1}:", [hex(x) for x in devices])
    finally:
        i2c.unlock()
    
    try:
        # Create sensor object
        sensor = adafruit_vl53l1x.VL53L1X(i2c)
        print(f"Successfully created sensor {pin_number + 1}")
        
        # Change address if not the last sensor
        if pin_number < len(xshut) - 1:
            new_address = pin_number + 0x30
            print(f"Changing address of sensor {pin_number + 1} to {hex(new_address)}")
            sensor.set_address(new_address)
            time.sleep(0.1)
        
        # Configure sensor
        sensor.distance_mode = 1
        sensor.timing_budget = 50
        sensor.start_ranging()
        
        vl53l1x_sensors.append(sensor)
        print(f"Sensor {pin_number + 1} initialized successfully")
        
    except Exception as e:
        print(f"Error initializing sensor {pin_number + 1}:", str(e))
        continue

# Verify final I2C configuration
while not i2c.try_lock():
    pass
try:
    print("Final I2C scan:", [hex(x) for x in i2c.scan()])
finally:
    i2c.unlock()

if not vl53l1x_sensors:
    raise RuntimeError("No sensors were successfully initialized!")

print(f"Successfully initialized {len(vl53l1x_sensors)} sensors")

def map_range(x, in_min, in_max, out_min, out_max):
    x = min(max(x, in_min), in_max)
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

# State variables
filtered_values = [0.0] * len(vl53l1x_sensors)
last_midi_values = [-1] * len(vl53l1x_sensors)

while True:
    for i, sensor in enumerate(vl53l1x_sensors):
        try:
            # Read sensor
            distance = sensor.distance
            if distance is None:
                distance = 0
            
            # Apply exponential smoothing filter
            filtered_values[i] = (ALPHA * distance) + ((1 - ALPHA) * filtered_values[i])
            
            # Map to MIDI range (0-127)
            midi_value = map_range(filtered_values[i], 0, 500, 0, 127)
            
            # Send MIDI CC if value has changed
            if midi_value != last_midi_values[i]:
                cc_number = MIDI_CC_1 if i == 0 else MIDI_CC_2
                midi.send(ControlChange(cc_number, midi_value))
                last_midi_values[i] = midi_value
                print(f"Sensor {i+1}: {filtered_values[i]:.1f}mm -> CC{cc_number}: {midi_value}")
                
        except Exception as e:
            print(f"Error reading sensor {i+1}:", str(e))
            continue
            
    time.sleep(0.05)