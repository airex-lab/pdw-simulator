import numpy as np
from pint import UnitRegistry

# Create a unit registry
ureg = UnitRegistry(autoconvert_offset_to_baseunit=True)

def move_straight_line(start_position, current_time, velocity=None, start_time=None):
    """
    Calculate the position of an object, either stationary or moving along a straight line.
    
    :param start_position: Initial position [x, y] in meters
    :param current_time: Current time in seconds
    :param velocity: Optional - Velocity [vx, vy] in meters per second for moving objects
    :param start_time: Optional - Start time in seconds for moving objects
    :return: Current position [x, y] in meters
    """
    initial_position = np.array(start_position) * ureg.meter
    
    if velocity is None or start_time is None:
        # Object is stationary
        return initial_position
    else:
        # Object is moving
        velocity = np.array(velocity) * ureg('meter/second')
        elapsed_time = (current_time - start_time) * ureg.second
        displacement = velocity * elapsed_time
        return initial_position + displacement

def calculate_trajectory(start_position, end_time, time_step, velocity=None, start_time=None):
    """
    Calculate the trajectory of an object, either stationary or moving along a straight line.
    
    :param start_position: Initial position [x, y] in meters
    :param end_time: End time of the trajectory in seconds
    :param time_step: Time step for trajectory calculation in seconds
    :param velocity: Optional - Velocity [vx, vy] in meters per second for moving objects
    :param start_time: Optional - Start time in seconds for moving objects
    :return: List of [time, x, y] points
    """
    trajectory = []
    current_time = start_time if start_time is not None else 0
    
    while current_time <= end_time:
        position = move_straight_line(start_position, current_time, velocity, start_time)
        trajectory.append([current_time, position[0].magnitude, position[1].magnitude])
        current_time += time_step
    
    return trajectory

# Export the unit registry so it can be imported in other files
def get_unit_registry():
    return ureg