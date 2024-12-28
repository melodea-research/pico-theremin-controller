import usb_midi
import board
import time
import busio
import digitalio
import adafruit_midi
import adafruit_vl53l1x
from adafruit_midi.control_change import ControlChange

class ValueFilter:
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.filtered_value = None
        
    def update(self, new_value):
        if self.filtered_value is None:
            self.filtered_value = new_value
        else:
            self.filtered_value = (self.alpha * new_value + 
                                 (1 - self.alpha) * self.filtered_value)
        return self.filtered_value

class MIDIController:
    def __init__(self, midi_in_port=0, midi_out_port=1, channel=0):
        self.midi = adafruit_midi.MIDI(
            midi_in=usb_midi.ports[midi_in_port],
            in_channel=channel,
            midi_out=usb_midi.ports[midi_out_port],
            out_channel=channel
        )
        self.last_sent_values = {}
        
    def send_cc(self, cc_number, value, force=False):
        # Only send if value has changed or force flag is True
        current_value = int(value)
        if force or self.last_sent_values.get(cc_number) != current_value:
            self.midi.send(ControlChange(cc_number, current_value))
            self.last_sent_values[cc_number] = current_value
            print(f"Sent MIDI CC {cc_number}: {current_value}")

class DistanceSensor:
    MIN_DISTANCE = 10  # mm
    MAX_DISTANCE = 300  # mm
    
    def __init__(self, i2c, xshut_pin, sensor_number, base_address=0x30):
        self.sensor_number = sensor_number
        self.xshut = digitalio.DigitalInOut(xshut_pin)
        self.xshut.switch_to_output(value=False)
        self.filter = ValueFilter()
        
        # Initialize sensor
        self.xshut.value = True
        time.sleep(0.1)  # Add small delay after enabling sensor
        self.sensor = adafruit_vl53l1x.VL53L1X(i2c)
        if sensor_number < 255:  # Avoid changing address of last sensor
            self.sensor.set_address(base_address + sensor_number)
            
    def start(self):
        try:
            self.sensor.start_ranging()
        except Exception as e:
            print(f"Error starting sensor {self.sensor_number}: {e}")
            
    def read(self):
        try:
            if self.sensor.data_ready:
                raw_distance = self.sensor.distance
                if raw_distance is None:
                    print(f"Sensor {self.sensor_number} returned None")
                    return None
                
                self.sensor.clear_interrupt()
                
                clamped_distance = max(self.MIN_DISTANCE, 
                                     min(self.MAX_DISTANCE, raw_distance))
                
                filtered_distance = self.filter.update(clamped_distance)
                
                midi_value = int((filtered_distance - self.MIN_DISTANCE) * 127 / 
                               (self.MAX_DISTANCE - self.MIN_DISTANCE))
                return max(0, min(127, midi_value))
            return None
        except Exception as e:
            print(f"Error reading sensor {self.sensor_number}: {e}")
            return None

class SensorArray:
    def __init__(self):
        # I2C Setup
        self.i2c = busio.I2C(board.GP5, board.GP4)  # SCL, SDA
        
        xshut_pins = [board.GP2, board.GP3]
        self.sensors = []
        self.midi_controller = MIDIController()
        
        for i, pin in enumerate(xshut_pins):
            try:
                sensor = DistanceSensor(self.i2c, pin, i)
                self.sensors.append(sensor)
            except Exception as e:
                print(f"Error initializing sensor {i}: {e}")
        
        if self.i2c.try_lock():
            print("Sensor I2C addresses:", [hex(x) for x in self.i2c.scan()])
            self.i2c.unlock()
        
        for sensor in self.sensors:
            sensor.start()
    
    def update(self):
        for i, sensor in enumerate(self.sensors):
            value = sensor.read()
            if value is not None:
                self.midi_controller.send_cc(20 + i, value)

def main():
    try:
        sensor_array = SensorArray()
        print("Initialization complete, starting main loop...")
        
        while True:
            sensor_array.update()
            time.sleep(0.01)

    except Exception as e:
        print(f"Main loop error: {e}")
        raise  # Re-raise the exception for debugging

main()