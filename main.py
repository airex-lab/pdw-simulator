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
        print(f"Added {radar.name} to scenario")
    
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
    time_window = 0.0001 * ureg.second  # 100 microsecond window
    pulse_time = radar.get_next_pulse_time(current_time)
    print(f"Next pulse time for {radar.name}: {pulse_time}")
    if pulse_time is None or pulse_time > current_time + time_window:
        print(f"No pulse generated for {radar.name} at {current_time}")
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
    """
    Brief Explanation 
    
    """
    config = load_config('config.yaml')
    scenario = create_scenario(config)
    
    output_file = 'pdw_output.csv'
    run_simulation(scenario, output_file)
    
    print(f"Simulation complete. PDW data written to {output_file}")

if __name__ == "__main__":
    main()

