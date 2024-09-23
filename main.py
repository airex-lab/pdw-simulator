import yaml
import numpy as np
from scenario_geometry_functions import calculate_trajectory, get_unit_registry

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
        self.rotation_period = config['rotation_period'] * ureg.second
        self.pri = config['pri'] * ureg.second
        self.frequency = config['frequency'] * ureg.hertz
        self.pulse_width = config['pulse_width'] * ureg.second
        self.power = config['power'] * ureg.watt
        self.trajectory = None
        self.current_position = self.start_position

    def calculate_trajectory(self, end_time, time_step):
        if np.any(self.velocity != 0):
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude,
                self.velocity.magnitude, self.start_time.magnitude)
        else:
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude)

    def update_position(self, current_time):
        if self.trajectory is not None:
            idx = np.searchsorted([t[0] for t in self.trajectory], current_time.magnitude)
            if idx < len(self.trajectory):
                self.current_position = np.array([self.trajectory[idx][1], self.trajectory[idx][2]]) * ureg.meter

class Sensor:
    def __init__(self, config):
        self.name = config['name']
        self.start_position = np.array(config['start_position']) * ureg.meter
        self.velocity = np.array(config.get('velocity', [0, 0])) * ureg('meter/second')
        self.start_time = config.get('start_time', 0) * ureg.second
        self.detection_probability = config['detection_probability']
        self.measurement_error = {
            'amplitude': config['measurement_error']['amplitude'],
            'toa': config['measurement_error']['toa'] * ureg.second,
            'frequency': config['measurement_error']['frequency'] * ureg.hertz,
            'pulse_width': config['measurement_error']['pulse_width'] * ureg.second,
            'aoa': config['measurement_error']['aoa'] * ureg.degree
        }
        self.trajectory = None
        self.current_position = self.start_position

    def calculate_trajectory(self, end_time, time_step):
        if np.any(self.velocity != 0):
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude,
                self.velocity.magnitude, self.start_time.magnitude)
        else:
            self.trajectory = calculate_trajectory(
                self.start_position.magnitude, end_time.magnitude, time_step.magnitude)

    def update_position(self, current_time):
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

def main():
    config = load_config('config.yaml')
    scenario = create_scenario(config)
    
    print(f"Scenario: {scenario.start_time} to {scenario.end_time}")
    
    while scenario.current_time <= scenario.end_time:
        print(f"\nTime: {scenario.current_time}")
        for radar in scenario.radars:
            print(f"Radar: {radar.name} at position {radar.current_position}")
        for sensor in scenario.sensors:
            print(f"Sensor: {sensor.name} at position {sensor.current_position}")
        scenario.update()

if __name__ == "__main__":
    main()