import yaml
import numpy as np
from scenario_geometry_functions import calculate_trajectory, get_unit_registry
from radar_properties import *
from sensor_properties import *

# Get the unit registry from scenario_geometry_functions
ureg = get_unit_registry()

class Scenario:
    def __init__(self, config):
        self.start_time = config['start_time'] * ureg.second
        self.end_time = config['end_time'] * ureg.second
        self.time_step = config['time_step'] * ureg.second
        self.current_time = self.start_time
        self.radars = []
        self.sensors = []

    def update(self):
        self.current_time += self.time_step
        for radar in self.radars:
            radar.update_position(self.current_time)
        for sensor in self.sensors:
            sensor.update_position(self.current_time)

class Radar:
    def __init__(self, config):
        self.name = config['name']
        self.start_position = np.array(config['start_position']) * ureg.meter
        self.velocity = np.array(config.get('velocity', [0, 0])) * ureg('meter/second')
        self.start_time = config.get('start_time', 0) * ureg.second
        self.current_time = self.start_time
        
        # Rotation period parameters
        self.rotation_type = config['rotation_type']
        self.rotation_params = config['rotation_params']
        self.rotation_data = None
        self.current_angle = self.rotation_params['alpha0']
        self.current_period = self.rotation_params['T_rot'] * ureg.second
        # self.frequency = config['frequency'] * ureg.hertz
        # self.pulse_width = config['pulse_width'] * ureg.second
        self.power = config['power'] * ureg.watt
        self.trajectory = None
        self.current_position = self.start_position

        ## PRI 
        self.pri_type=config['pri_type']
        self.pri_params=config['pri_params']
        self.pulse_times=None


        ## Frequency 
        self.frequency_type = config['frequency_type']
        self.frequency_params = config['frequency_params']
        self.pulse_width_type = config['pulse_width_type']
        self.pulse_width_params = config['pulse_width_params']
        self.frequencies = None
        self.pulse_widths = None


        #Antenna Lobe pattern
        self.lobe_pattern_type = config['lobe_pattern']['type']
        if self.lobe_pattern_type == 'Sinc':
            self.theta_ml = config['lobe_pattern']['main_lobe_opening_angle'] * ureg.degree
            self.P_ml = config['lobe_pattern']['radar_power_at_main_lobe'] * ureg.dB
            self.P_bl = config['lobe_pattern']['radar_power_at_back_lobe'] * ureg.dB


    
    def calculate_power_at_angle(self, theta):
        if self.lobe_pattern_type == 'Sinc':
            return sinc_lobe_pattern(theta, self.theta_ml, self.P_ml, self.P_bl)
        else:
            raise ValueError(f"Unsupported lobe pattern type: {self.lobe_pattern_type}")

    def get_current_angle(self):
        return self.current_angle * ureg.radian

    def get_current_period(self):
        return self.current_period
    
    def calculate_pulse_times(self, end_time):
        if self.pri_type == 'fixed':
            self.pulse_times = fixed_pri(self.start_time.magnitude, end_time.magnitude, self.pri_params['pri'])
        elif self.pri_type == 'stagger':
            self.pulse_times = stagger_pri(self.start_time.magnitude, end_time.magnitude, self.pri_params['pri_pattern'])
        elif self.pri_type == 'switched':
            self.pulse_times = switched_pri(self.start_time.magnitude, end_time.magnitude, 
                                            self.pri_params['pri_pattern'], self.pri_params['repetitions'])
        elif self.pri_type == 'jitter':
            self.pulse_times = jitter_pri(self.start_time.magnitude, end_time.magnitude, 
                                          self.pri_params['mean_pri'], self.pri_params['jitter_percentage'])
        else:
            raise ValueError(f"Invalid PRI type: {self.pri_type}")
        
    def calculate_frequencies(self, end_time):
            if self.frequency_type == 'fixed':
                self.frequencies = fixed_frequency(self.start_time.magnitude, end_time.magnitude, self.frequency_params['frequency'])
            elif self.frequency_type == 'stagger':
                self.frequencies = stagger_frequency(self.start_time.magnitude, end_time.magnitude, self.frequency_params['frequency_pattern'])
            elif self.frequency_type == 'switched':
                self.frequencies = switched_frequency(self.start_time.magnitude, end_time.magnitude, 
                                                    self.frequency_params['frequency_pattern'], self.frequency_params['repetitions'])
            elif self.frequency_type == 'jitter':
                self.frequencies = jitter_frequency(self.start_time.magnitude, end_time.magnitude, 
                                                    self.frequency_params['mean_frequency'], self.frequency_params['jitter_percentage'])
            else:
                raise ValueError(f"Invalid frequency type: {self.frequency_type}")

    def calculate_pulse_widths(self, end_time):
        if self.pulse_width_type == 'fixed':
            self.pulse_widths = fixed_pulse_width(self.start_time.magnitude, end_time.magnitude, self.pulse_width_params['pulse_width'])
        elif self.pulse_width_type == 'stagger':
            self.pulse_widths = stagger_pulse_width(self.start_time.magnitude, end_time.magnitude, self.pulse_width_params['pulse_width_pattern'])
        elif self.pulse_width_type == 'switched':
            self.pulse_widths = switched_pulse_width(self.start_time.magnitude, end_time.magnitude, 
                                                     self.pulse_width_params['pulse_width_pattern'], self.pulse_width_params['repetitions'])
        elif self.pulse_width_type == 'jitter':
            self.pulse_widths = jitter_pulse_width(self.start_time.magnitude, end_time.magnitude, 
                                                   self.pulse_width_params['mean_pulse_width'], self.pulse_width_params['jitter_percentage'])
        else:
            raise ValueError(f"Invalid pulse width type: {self.pulse_width_type}")
        
    def calculate_trajectory(self, end_time, time_step):
        if np.any(self.velocity != 0):
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude,
                self.velocity.magnitude, self.start_time.magnitude)
        else:
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude)
            
        self.calculate_pulse_times(end_time)
        self.calculate_frequencies(end_time)
        self.calculate_pulse_widths(end_time)
        
        # Calculate rotation angles and periods
        self.rotation_data = calculate_rotation_angles(
            self.start_time.magnitude, end_time.magnitude, time_step.magnitude,
            self.rotation_type, self.rotation_params)

    def update_position(self, current_time):
        if self.trajectory is not None:
            idx = np.searchsorted([t[0] for t in self.trajectory], current_time.magnitude)
            if idx < len(self.trajectory):
                self.current_position = np.array([self.trajectory[idx][1], self.trajectory[idx][2]]) * ureg.meter
        
        # Update rotation angle and period
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], current_time.magnitude)
            if idx < len(self.rotation_data):
                self.current_angle = self.rotation_data[idx][1]
                self.current_period = self.rotation_data[idx][2] * ureg.second


    def get_current_angle(self):
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], self.current_time.magnitude)
            if idx < len(self.rotation_data):
                return self.rotation_data[idx][1] * ureg.radian
        return 0 * ureg.radian

    def get_current_period(self):
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], self.current_time.magnitude)
            if idx < len(self.rotation_data):
                return self.rotation_data[idx][2] * ureg.second
        return self.rotation_params['T_rot'] * ureg.second
    
    def update(self, current_time):
        self.current_time = current_time
        self.update_position(current_time)
        self.update_rotation(current_time)

    def update_position(self, current_time):
        if self.trajectory is not None:
            idx = np.searchsorted([t[0] for t in self.trajectory], current_time.magnitude)
            if idx < len(self.trajectory):
                self.current_position = np.array([self.trajectory[idx][1], self.trajectory[idx][2]]) * ureg.meter

    def update_rotation(self, current_time):
        if self.rotation_data is not None:
            idx = np.searchsorted([t[0] for t in self.rotation_data], current_time.magnitude)
            if idx < len(self.rotation_data):
                self.current_angle = self.rotation_data[idx][1]
                self.current_period = self.rotation_data[idx][2] * ureg.second

    def get_current_angle(self):
        return self.current_angle * ureg.radian

    def get_current_period(self):
        return self.current_period


class Sensor:
    def __init__(self, config):
        self.name = config['name']
        self.start_position = np.array(config['start_position']) * ureg.meter
        self.velocity = np.array(config.get('velocity', [0, 0])) * ureg('meter/second')
        self.start_time = config.get('start_time', 0) * ureg.second
        self.trajectory = None
        self.current_position = self.start_position
        self.current_time = self.start_time

        # Detection Probability and Saturation Level
        self.saturation_level = config['saturation_level'] * ureg.dB
        self.detection_levels = np.array(config['detection_probability']['level']) * ureg.dB
        self.detection_probabilities = np.array(config['detection_probability']['probability']) / 100

        # Error models
        self.amplitude_error_syst = create_error_model(config['amplitude_error']['systematic'])
        self.amplitude_error_arb = create_error_model(config['amplitude_error']['arbitrary'])
        self.toa_error_syst = create_error_model(config['toa_error']['systematic'])
        self.toa_error_arb = create_error_model(config['toa_error']['arbitrary'])
        self.frequency_error_syst = create_error_model(config['frequency_error']['systematic'])
        self.frequency_error_arb = create_error_model(config['frequency_error']['arbitrary'])
        self.pw_error_syst = create_error_model(config['pulse_width_error']['systematic'])
        self.pw_error_arb = create_error_model(config['pulse_width_error']['arbitrary'])
        self.aoa_error_syst = create_error_model(config['aoa_error']['systematic'])
        self.aoa_error_arb = create_error_model(config['aoa_error']['arbitrary'])

    def detect_pulse(self, amplitude):
        return detect_pulse(amplitude, self.detection_levels, self.detection_probabilities, self.saturation_level)

    def measure_amplitude(self, true_amplitude, r, P_theta, t, P0):
        return measure_amplitude(true_amplitude, r, P_theta, t, P0, self.amplitude_error_syst, self.amplitude_error_arb)

    def measure_toa(self, true_toa, r, t):
        return measure_toa(true_toa, r, t, self.toa_error_syst, self.toa_error_arb)

    def measure_frequency(self, true_frequency, t):
        return measure_frequency(true_frequency, t, self.frequency_error_syst, self.frequency_error_arb)

    def measure_pulse_width(self, true_pw, t):
        return measure_pulse_width(true_pw, t, self.pw_error_syst, self.pw_error_arb)

    def measure_aoa(self, true_aoa, t):
        return measure_aoa(true_aoa, t, self.aoa_error_syst, self.aoa_error_arb)

    def calculate_trajectory(self, end_time, time_step):
        if np.any(self.velocity != 0):
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude,
                self.velocity.magnitude, self.start_time.magnitude)
        else:
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude)

    def update_position(self, current_time):
        self.current_time = current_time
        if self.trajectory is not None:
            idx = np.searchsorted([t[0] for t in self.trajectory], current_time.magnitude)
            if idx < len(self.trajectory):
                self.current_position = np.array([self.trajectory[idx][1], self.trajectory[idx][2]]) * ureg.meter

def load_config(filename):
    with open(filename, 'r') as file:
        return yaml.safe_load(file)

def create_scenario(config):
    scenario = Scenario(config['scenario'])
    
    for radar_config in config['radars']:
        radar = Radar(radar_config)
        radar.calculate_trajectory(scenario.end_time, scenario.time_step)
        scenario.radars.append(radar)
    
    for sensor_config in config['sensors']:
        sensor = Sensor(sensor_config)
        sensor.calculate_trajectory(scenario.end_time, scenario.time_step)
        scenario.sensors.append(sensor)
    
    return scenario

def print_sensor_properties(sensors):
    for sensor in sensors:
        print(f"\n{'='*20} Sensor: {sensor.name} {'='*20}")
        print(f"Position: {sensor.current_position}")
        print(f"Saturation Level: {sensor.saturation_level}")
        
        print("\nDetection Probability:")
        for level, prob in zip(sensor.detection_levels, sensor.detection_probabilities):
            print(f"  {level:.2f}: {prob*100:.1f}%")
        
        print("\nAmplitude Error:")
        print(f"  Systematic: {sensor.amplitude_error_syst(0):.2f}")
        print(f"  Arbitrary: {sensor.amplitude_error_arb(1)[0]:.2f} (example)")
        
        print("\nTOA Error:")
        print(f"  Systematic: {sensor.toa_error_syst(0):.2e}")
        print(f"  Arbitrary: {sensor.toa_error_arb(1)[0]:.2e} (example)")
        
        print("\nFrequency Error:")
        print(f"  Systematic: {sensor.frequency_error_syst(0):.2e}")
        print(f"  Arbitrary: {sensor.frequency_error_arb(1)[0]:.2e} (example)")
        
        print("\nPulse Width Error:")
        print(f"  Systematic: {sensor.pw_error_syst(0):.2e}")
        print(f"  Arbitrary: {sensor.pw_error_arb(1)[0]:.2e} (example)")
        
        print("\nAOA Error:")
        print(f"  Systematic: {sensor.aoa_error_syst(0):.2f}")
        print(f"  Arbitrary: {sensor.aoa_error_arb(1)[0]:.2f} (example)")
        
        print(f"{'='*50}")

def main():
    config = load_config('config.yaml')
    scenario = create_scenario(config)
    
    print(f"Scenario: {scenario.start_time} to {scenario.end_time}")
    
    while scenario.current_time <= scenario.end_time:
        print(f"\nTime: {scenario.current_time}")
        for radar in scenario.radars:
            print(f"Radar: {radar.name}")
            print(f"  Position: {radar.current_position}")
            try:
                print(f"  Rotation angle: {radar.get_current_angle():.2f}")
                print(f"  Rotation period: {radar.get_current_period():.6f}")
            except AttributeError as e:
                print(f"  Error getting rotation data: {e}")
            
            # Print PRI information
            if hasattr(radar, 'pulse_times') and radar.pulse_times is not None and len(radar.pulse_times) > 1:
                current_pri = radar.pulse_times[1] - radar.pulse_times[0]
                print(f"  Current PRI: {current_pri:.6f} seconds")
            else:
                print("  No pulse times available")
            
            # Print Frequency information
            if hasattr(radar, 'frequencies') and radar.frequencies is not None and len(radar.frequencies) > 0:
                current_freq = radar.frequencies[0]
                try:
                    print(f"  Current Frequency: {float(current_freq):.2e} Hz")
                except ValueError:
                    print(f"  Current Frequency: {current_freq} Hz")
            else:
                print("  No frequency data available")
            
            # Print Pulse Width information
            if hasattr(radar, 'pulse_widths') and radar.pulse_widths is not None and len(radar.pulse_widths) > 0:
                current_pw = radar.pulse_widths[0]
                try:
                    print(f"  Current Pulse Width: {float(current_pw):.9f} seconds")
                except ValueError:
                    print(f"  Current Pulse Width: {current_pw} seconds")
            else:
                print("  No pulse width data available")
        
        for sensor in scenario.sensors:
            print(f"Sensor: {sensor.name}")
            print(f"  Position: {sensor.current_position}")
        
        # Print a separator for readability
        print("-" * 50)
        
        scenario.update()

    print_sensor_properties(scenario.sensors)
    # After the simulation, print some statistics
    print("\nSimulation Summary:")
    for radar in scenario.radars:
        print(f"\nRadar: {radar.name}")
        if hasattr(radar, 'pulse_times') and radar.pulse_times is not None:
            print(f"  Total pulses: {len(radar.pulse_times)}")
            print(f"  PRI range: {min(np.diff(radar.pulse_times)):.6f} to {max(np.diff(radar.pulse_times)):.6f} seconds")
        if hasattr(radar, 'frequencies') and radar.frequencies is not None:
            try:
                freq_min = min(float(f) for f in radar.frequencies)
                freq_max = max(float(f) for f in radar.frequencies)
                print(f"  Frequency range: {freq_min:.2e} to {freq_max:.2e} Hz")
            except ValueError:
                print(f"  Frequency range: {min(radar.frequencies)} to {max(radar.frequencies)} Hz")
        if hasattr(radar, 'pulse_widths') and radar.pulse_widths is not None:
            try:
                pw_min = min(float(pw) for pw in radar.pulse_widths)
                pw_max = max(float(pw) for pw in radar.pulse_widths)
                print(f"  Pulse width range: {pw_min:.9f} to {pw_max:.9f} seconds")
            except ValueError:
                print(f"  Pulse width range: {min(radar.pulse_widths)} to {max(radar.pulse_widths)} seconds")

# if __name__ == "__main__":
#     theta_range = np.linspace(-np.pi, np.pi, 1000) * ureg.radian
#     theta_ml = 10 * ureg.degree
#     P_ml = 0 * ureg.dB
#     P_bl = -20 * ureg.dB

#     P_theta = sinc_lobe_pattern(theta_range, theta_ml, P_ml, P_bl)

#     import matplotlib.pyplot as plt

#     plt.figure(figsize=(10, 6))
#     plt.plot(theta_range.to(ureg.degree).magnitude, P_theta.magnitude)
#     plt.title("Radar Antenna Lobe Pattern")
#     plt.xlabel("Angle (degrees)")
#     plt.ylabel("Relative Power (dB)")
#     plt.ylim(-50, 5)
#     plt.grid(True)
#     plt.show()

if __name__ == "__main__":
    main()