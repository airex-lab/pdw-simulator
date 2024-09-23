import numpy as np
from scipy import stats
from scenario_geometry_functions import get_unit_registry

ureg = get_unit_registry()

def constant_rotation_period(t, t0, alpha0, T_rot):
    """
    Calculate the angle for constant rotation period.
    
    :param t: Current time
    :param t0: Start time
    :param alpha0: Initial angle at t0
    :param T_rot: Rotation period
    :return: Current angle
    """
    return alpha0 + 2 * np.pi * (t - t0) / T_rot

def varying_rotation_period(t, t0, alpha0, T_rot, A, s, phi0):
    """
    Calculate the angle for varying rotation period.
    
    :param t: Current time
    :param t0: Start time
    :param alpha0: Initial angle at t0
    :param T_rot: Constant component of rotation period
    :param A: Amplitude of variation relative to constant component
    :param s: Angular frequency of variation relative to constant component
    :param phi0: Start phase of variation
    :return: Current angle
    """
    omega0 = 2 * np.pi / T_rot
    B = (A / s) * (np.cos(s * omega0 * t0 + phi0) - np.cos(phi0))
    return alpha0 + omega0 * (t - t0) - (A / s) * np.cos(s * omega0 * t + phi0) + B

def calculate_varying_period(t, T_rot, A, s, phi0):
    """
    Calculate the varying rotation period.
    
    :param t: Current time
    :param T_rot: Constant component of rotation period
    :param A: Amplitude of variation relative to constant component
    :param s: Angular frequency of variation relative to constant component
    :param phi0: Start phase of variation
    :return: Current rotation period
    """
    omega0 = 2 * np.pi / T_rot
    return T_rot / (1 + A * np.sin(s * omega0 * t + phi0))

def calculate_rotation_angles(start_time, end_time, time_step, rotation_type, params):
    """
    Calculate rotation angles and periods over time.
    
    :param start_time: Start time of calculation
    :param end_time: End time of calculation
    :param time_step: Time step for calculation
    :param rotation_type: 'constant' or 'varying'
    :param params: Dictionary of parameters for the rotation calculation
    :return: List of [time, angle, period] triples
    """
    times = np.arange(start_time, end_time + time_step, time_step)
    if rotation_type == 'constant':
        angles = constant_rotation_period(times, params['t0'], params['alpha0'], params['T_rot'])
        periods = np.full_like(times, params['T_rot'])
    elif rotation_type == 'varying':
        angles = varying_rotation_period(times, params['t0'], params['alpha0'], params['T_rot'], 
                                         params['A'], params['s'], params['phi0'])
        periods = calculate_varying_period(times, params['T_rot'], params['A'], params['s'], params['phi0'])
    else:
        raise ValueError("Invalid rotation type. Must be 'constant' or 'varying'.")
    
    return list(zip(times, angles, periods))



########## Pulse Repetition Interval ############ 
# Fixed PRI
# Stagger PRI
# Switched PRI
#Jitter PRI 


def fixed_pri(start_time, end_time, pri):
    """
    Generate fixed PRI pulses.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pri: Fixed PRI value (seconds)
    :return: Array of pulse times
    """
    return np.arange(start_time, end_time, pri)

def stagger_pri(start_time, end_time, pri_pattern):
    """
    Generate stagger PRI pulses.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pri_pattern: List of PRI values for the stagger pattern (seconds)
    :return: Array of pulse times
    """
    pulse_times = []
    current_time = start_time
    pri_index = 0
    
    while current_time < end_time:
        pulse_times.append(current_time)
        current_time += pri_pattern[pri_index]
        pri_index = (pri_index + 1) % len(pri_pattern)
    
    return np.array(pulse_times)

def switched_pri(start_time, end_time, pri_pattern, repetitions):
    """
    Generate switched PRI pulses.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pri_pattern: List of PRI values for the switched pattern (seconds)
    :param repetitions: List of repetition counts for each PRI value
    :return: Array of pulse times
    """
    pulse_times = []
    current_time = start_time
    
    while current_time < end_time:
        for pri, rep in zip(pri_pattern, repetitions):
            for _ in range(rep):
                if current_time >= end_time:
                    break
                pulse_times.append(current_time)
                current_time += pri
    
    return np.array(pulse_times)

def jitter_pri(start_time, end_time, mean_pri, jitter_percentage):
    """
    Generate jitter PRI pulses.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param mean_pri: Mean PRI value (seconds)
    :param jitter_percentage: Jitter as a percentage of mean PRI
    :return: Array of pulse times
    """
    pulse_times = []
    current_time = start_time
    
    std_dev = mean_pri * (jitter_percentage / 100)
    
    while current_time < end_time:
        pulse_times.append(current_time)
        jittered_pri = stats.truncnorm(
            (0 - mean_pri) / std_dev,
            (np.inf - mean_pri) / std_dev,
            loc=mean_pri,
            scale=std_dev
        ).rvs()
        current_time += jittered_pri
    
    return np.array(pulse_times)

######### Frequency Functions 

# Frequency functions
def fixed_frequency(start_time, end_time, frequency):
    """
    Generate fixed frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param frequency: Fixed frequency value (Hz)
    :return: Array of frequency values
    """
    return np.full(int((end_time - start_time) / 0.001), frequency)  # Assuming 1ms intervals

def stagger_frequency(start_time, end_time, frequency_pattern):
    """
    Generate stagger frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param frequency_pattern: List of frequency values for the stagger pattern (Hz)
    :return: Array of frequency values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(frequency_pattern, num_values // len(frequency_pattern) + 1)[:num_values]

def switched_frequency(start_time, end_time, frequency_pattern, repetitions):
    """
    Generate switched frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param frequency_pattern: List of frequency values for the switched pattern (Hz)
    :param repetitions: List of repetition counts for each frequency value
    :return: Array of frequency values
    """
    frequencies = []
    for freq, rep in zip(frequency_pattern, repetitions):
        frequencies.extend([freq] * rep)
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(frequencies, num_values // len(frequencies) + 1)[:num_values]

def jitter_frequency(start_time, end_time, mean_frequency, jitter_percentage):
    """
    Generate jitter frequency values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param mean_frequency: Mean frequency value (Hz)
    :param jitter_percentage: Jitter as a percentage of mean frequency
    :return: Array of frequency values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    std_dev = mean_frequency * (jitter_percentage / 100)
    return stats.truncnorm(
        (0 - mean_frequency) / std_dev,
        (np.inf - mean_frequency) / std_dev,
        loc=mean_frequency,
        scale=std_dev
    ).rvs(size=num_values)


########### - Pulse Width Functions - ############
# Pulse width functions
def fixed_pulse_width(start_time, end_time, pulse_width):
    """
    Generate fixed pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pulse_width: Fixed pulse width value (seconds)
    :return: Array of pulse width values
    """
    return np.full(int((end_time - start_time) / 0.001), pulse_width)  # Assuming 1ms intervals

def stagger_pulse_width(start_time, end_time, pulse_width_pattern):
    """
    Generate stagger pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pulse_width_pattern: List of pulse width values for the stagger pattern (seconds)
    :return: Array of pulse width values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(pulse_width_pattern, num_values // len(pulse_width_pattern) + 1)[:num_values]

def switched_pulse_width(start_time, end_time, pulse_width_pattern, repetitions):
    """
    Generate switched pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param pulse_width_pattern: List of pulse width values for the switched pattern (seconds)
    :param repetitions: List of repetition counts for each pulse width value
    :return: Array of pulse width values
    """
    pulse_widths = []
    for pw, rep in zip(pulse_width_pattern, repetitions):
        pulse_widths.extend([pw] * rep)
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    return np.tile(pulse_widths, num_values // len(pulse_widths) + 1)[:num_values]

def jitter_pulse_width(start_time, end_time, mean_pulse_width, jitter_percentage):
    """
    Generate jitter pulse width values.
    
    :param start_time: Start time of the simulation (seconds)
    :param end_time: End time of the simulation (seconds)
    :param mean_pulse_width: Mean pulse width value (seconds)
    :param jitter_percentage: Jitter as a percentage of mean pulse width
    :return: Array of pulse width values
    """
    num_values = int((end_time - start_time) / 0.001)  # Assuming 1ms intervals
    std_dev = mean_pulse_width * (jitter_percentage / 100)
    return stats.truncnorm(
        (0 - mean_pulse_width) / std_dev,
        (np.inf - mean_pulse_width) / std_dev,
        loc=mean_pulse_width,
        scale=std_dev
    ).rvs(size=num_values)



######### - Radar Antenna Lobe Pattern - ###########

def sinc_lobe_pattern(theta, theta_ml, P_ml, P_bl):
    """
    Calculate the radar antenna lobe pattern using a modified sinc function.
    
    :param theta: Angle from the antenna boresight (in radians)
    :param theta_ml: Main lobe opening angle (in radians)
    :param P_ml: Radar power at main lobe (in dB)
    :param P_bl: Radar power at back lobe (in dB)
    :return: Power at the given angle (in dB)
    """
    # Convert inputs to appropriate units
    theta = theta.to(ureg.radian).magnitude
    theta_ml = theta_ml.to(ureg.radian).magnitude
    P_ml = P_ml.to(ureg.dB).magnitude
    P_bl = P_bl.to(ureg.dB).magnitude

    # Calculate x
    x = 0.443 * np.sin(theta) / np.sin(theta_ml / 2)

    # Calculate P_theta based on the range of theta
    P_theta = np.zeros_like(theta)

    # For theta in [-pi/2, pi/2]
    mask1 = np.abs(theta) <= np.pi/2
    P_theta[mask1] = 20 * np.log10(np.abs(np.sin(np.pi * x[mask1]) / (np.pi * x[mask1]))) + P_ml

    # For theta > pi/2
    mask2 = theta > np.pi/2
    P_theta[mask2] = 20 * np.log10(np.abs(np.sin(np.pi * x[mask2]) / (np.pi * x[mask2]))) + P_ml + 2/np.pi * P_bl * (theta[mask2] - np.pi/2)

    # For theta < -pi/2
    mask3 = theta < -np.pi/2
    P_theta[mask3] = 20 * np.log10(np.abs(np.sin(np.pi * x[mask3]) / (np.pi * x[mask3]))) + P_ml + 2/np.pi * P_bl * (-theta[mask3] - np.pi/2)

    return P_theta * ureg.dB