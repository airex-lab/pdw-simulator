import yaml
import numpy as np
from scenario_geometry_functions import calculate_trajectory, get_unit_registry
from radar_properties import *
from sensor_properties import *
from models import Scenario, Radar, Sensor
import sys

sys.stdout=open('output.txt','wt')
# Get the unit registry from scenario_geometry_functions
ureg = get_unit_registry()



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

def run_simulation(scenario, output_file):
    """
    Run the PDW simulation.

    :param scenario: Scenario object containing radars and sensors
    :param output_file: File to write PDW output
    """
    with open(output_file, 'w') as f:
        f.write("Time,SensorID,RadarID,TOA,Amplitude,Frequency,PulseWidth,AOA\n")

        while scenario.current_time <= scenario.end_time:
            print(f"Simulating time: {scenario.current_time}")
            scenario.update()

            for sensor in scenario.sensors:
                for radar in scenario.radars:
                    pdw = generate_pdw(sensor, radar, scenario.current_time)
                    if pdw:
                        f.write(f"{scenario.current_time.magnitude},{sensor.name},{radar.name},"
                                f"{pdw['TOA'].magnitude},{pdw['Amplitude'].magnitude},"
                                f"{pdw['Frequency'].magnitude},{pdw['PulseWidth'].magnitude},"
                                f"{pdw['AOA'].magnitude}\n")

            scenario.current_time += scenario.time_step

def generate_pdw(sensor, radar, current_time):
    # Calculate distance and angle between radar and sensor
    distance_vector = sensor.current_position - radar.current_position
    distance = np.linalg.norm(distance_vector) * ureg.meter
    distance=distance/ureg.meter
    angle = np.arctan2(distance_vector[1], distance_vector[0]) * ureg.radian

    # Check if a pulse is emitted at this time
    pulse_time = radar.get_next_pulse_time(current_time)
    if pulse_time is None or pulse_time > current_time:
        return None

    # Ensure pulse_time is a Pint Quantity
    pulse_time = ureg.Quantity(pulse_time).to(ureg.second)

    # Calculate true pulse parameters
    true_amplitude = radar.calculate_power_at_angle(angle).to(ureg.dB)
    speed_of_light = 299792458 * ureg.meter / ureg.second
    # print(f"Speed of light dimensionality: {speed_of_light.dimensionality}")
    # print(f"Pulse Time :{pulse_time.dimensionality}")
    # print(f"Distance Dimensionality: {distance.dimensionality}")
    true_toa = pulse_time + (distance / speed_of_light)
    true_frequency = radar.get_current_frequency()
    true_pw = radar.get_current_pulse_width()
    true_aoa = angle

    # Apply sensor detection and measurement
    if sensor.detect_pulse(true_amplitude):
        measured_amplitude = sensor.measure_amplitude(true_amplitude, distance, true_amplitude, current_time, radar.power)
        measured_toa = sensor.measure_toa(true_toa, distance, current_time)
        measured_frequency = sensor.measure_frequency(true_frequency, current_time)
        measured_pw = sensor.measure_pulse_width(true_pw, current_time)
        measured_aoa = sensor.measure_aoa(true_aoa, current_time)

        return {
            'TOA': measured_toa,
            'Amplitude': measured_amplitude,
            'Frequency': measured_frequency,
            'PulseWidth': measured_pw,
            'AOA': measured_aoa
        }
    else:
        return None


def main():
    config = load_config('config.yaml')
    scenario = create_scenario(config)
    
    output_file = 'pdw_output.csv'
    run_simulation(scenario, output_file)
    
    print(f"Simulation complete. PDW data written to {output_file}")

if __name__ == "__main__":
    main()

# def main():
#     config = load_config('config.yaml')
#     scenario = create_scenario(config)
#     # print(type(config))
#     # print(config.keys())
#     # print(type(config['sensors']))
#     # for i in range(0,len(config['sensors'])):
#     #     print(config['sensors'][i])
#     #     print('*'*5)
    
#     print(f"Scenario: {scenario.start_time} to {scenario.end_time}")
    
#     while scenario.current_time <= scenario.end_time:
#         print(f"\nTime: {scenario.current_time}")
#         for radar in scenario.radars:
#             print(f"Radar: {radar.name}")
#             print(f"  Position: {radar.current_position}")
#             try:
#                 print(f"  Rotation angle: {radar.get_current_angle():.2f}")
#                 print(f"  Rotation period: {radar.get_current_period():.6f}")
#             except AttributeError as e:
#                 print(f"  Error getting rotation data: {e}")
            
#             # Print PRI information
#             if hasattr(radar, 'pulse_times') and radar.pulse_times is not None and len(radar.pulse_times) > 1:
#                 current_pri = radar.pulse_times[1] - radar.pulse_times[0]
#                 print(f"  Current PRI: {current_pri:.6f} seconds")
#             else:
#                 print("  No pulse times available")
            
#             # Print Frequency information
#             if hasattr(radar, 'frequencies') and radar.frequencies is not None and len(radar.frequencies) > 0:
#                 current_freq = radar.frequencies[0]
#                 try:
#                     print(f"  Current Frequency: {float(current_freq):.2e} Hz")
#                 except ValueError:
#                     print(f"  Current Frequency: {current_freq} Hz")
#             else:
#                 print("  No frequency data available")
            
#             # Print Pulse Width information
#             if hasattr(radar, 'pulse_widths') and radar.pulse_widths is not None and len(radar.pulse_widths) > 0:
#                 current_pw = radar.pulse_widths[0]
#                 try:
#                     print(f"  Current Pulse Width: {float(current_pw):.9f} seconds")
#                 except ValueError:
#                     print(f"  Current Pulse Width: {current_pw} seconds")
#             else:
#                 print("  No pulse width data available")
        
#         for sensor in scenario.sensors:
#             print(f"Sensor: {sensor.name}")
#             print(f"  Position: {sensor.current_position}")
#             # Example values for testing measure_toa
#             true_toa = 1.0 * ureg.second
#             r = 1000 * ureg.meter
#             t = scenario.current_time

#             try:
#                 measured_toa = sensor.measure_toa(true_toa, r, t)
#                 print(f"  Measured TOA: {measured_toa}")
#             except Exception as e:
#                 print(f"  Error in measure_toa: {e}")
                
#                 # Print a separator for readability
#                 print("-" * 50)
        
#         scenario.update()

#     print_sensor_properties(scenario.sensors)
#     # After the simulation, print some statistics
#     print("\nSimulation Summary:")
#     for radar in scenario.radars:
#         print(f"\nRadar: {radar.name}")
#         if hasattr(radar, 'pulse_times') and radar.pulse_times is not None:
#             print(f"  Total pulses: {len(radar.pulse_times)}")
#             print(f"  PRI range: {min(np.diff(radar.pulse_times)):.6f} to {max(np.diff(radar.pulse_times)):.6f} seconds")
#         if hasattr(radar, 'frequencies') and radar.frequencies is not None:
#             try:
#                 freq_min = min(float(f) for f in radar.frequencies)
#                 freq_max = max(float(f) for f in radar.frequencies)
#                 print(f"  Frequency range: {freq_min:.2e} to {freq_max:.2e} Hz")
#             except ValueError:
#                 print(f"  Frequency range: {min(radar.frequencies)} to {max(radar.frequencies)} Hz")
#         if hasattr(radar, 'pulse_widths') and radar.pulse_widths is not None:
#             try:
#                 pw_min = min(float(pw) for pw in radar.pulse_widths)
#                 pw_max = max(float(pw) for pw in radar.pulse_widths)
#                 print(f"  Pulse width range: {pw_min:.9f} to {pw_max:.9f} seconds")
#             except ValueError:
#                 print(f"  Pulse width range: {min(radar.pulse_widths)} to {max(radar.pulse_widths)} seconds")

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

# if __name__ == "__main__":
#     main()