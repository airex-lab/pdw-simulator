import numpy as np
from scenario_geometry_functions import get_unit_registry

ureg = get_unit_registry()

def create_error_model(error_config):
    """
    Create an error model based on the configuration.
    
    :param error_config: Dictionary containing error model parameters
    :return: Function that generates errors based on the model
    """
    if error_config['type'] == 'constant':
        error_value, error_unit = parse_value_and_unit(error_config['error'])
        return lambda t: error_value * ureg(error_unit)
    elif error_config['type'] == 'linear':
        error_value, error_unit = parse_value_and_unit(error_config['error'])
        rate_value, rate_unit = parse_value_and_unit(error_config['rate'])
        return lambda t: (error_value + rate_value * t) * ureg(error_unit)
    elif error_config['type'] == 'sinus':
        A, A_unit = parse_value_and_unit(error_config['amplitude'])
        f = error_config['frequency']
        phi0 = error_config['phase']
        return lambda t: A * np.sin(2 * np.pi * f * t + phi0) * ureg(A_unit)
    elif error_config['type'] == 'gaussian':
        error_value, error_unit = parse_value_and_unit(error_config['error'])
        return lambda size: np.random.normal(0, error_value, size) * ureg(error_unit)
    else:
        raise ValueError(f"Unknown error type: {error_config['type']}")

def parse_value_and_unit(string_value):
    """
    Parse a string containing a value and a unit.
    
    :param string_value: String containing value and unit (e.g., '0.1 dB')
    :return: Tuple of (value, unit)
    """
    parts = string_value.split()
    if len(parts) == 2:
        return float(parts[0]), parts[1]
    elif len(parts) == 1:
        return float(parts[0]), ''
    else:
        raise ValueError(f"Invalid value and unit string: {string_value}")

def detect_pulse(amplitude, detection_levels, detection_probabilities, saturation_level):
    """
    Determine if a pulse is detected based on its amplitude.
    
    :param amplitude: Amplitude of the pulse
    :param detection_levels: List of detection levels
    :param detection_probabilities: List of detection probabilities corresponding to levels
    :param saturation_level: Saturation level of the sensor
    :return: Boolean indicating whether the pulse is detected
    """
    if amplitude > saturation_level:
        return True
    for level, prob in zip(detection_levels, detection_probabilities):
        if amplitude > level:
            return np.random.random() < prob
    return False

def measure_amplitude(true_amplitude, r, P_theta, t, P0, amplitude_error_syst, amplitude_error_arb):
    """
    Measure the amplitude of a detected pulse.
    
    :param true_amplitude: True amplitude of the pulse
    :param r: Distance between radar and sensor
    :param P_theta: Amplitude correction due to radar antenna lobe pattern
    :param t: Current time
    :param P0: Amplitude of an emitted pulse from an equivalent omnidirectional radar antenna
    :param amplitude_error_syst: Function to generate systematic error
    :param amplitude_error_arb: Function to generate arbitrary error
    :return: Measured amplitude
    """
    Pr = 20 * np.log10(r)
    P_syst = amplitude_error_syst(t)
    P_arb = amplitude_error_arb(1)[0]  # Generate a single random error
    
    measured_amplitude = P0 - Pr + P_theta + P_syst + P_arb
    return measured_amplitude.to(ureg.dB)

def measure_toa(true_toa, r, t, toa_error_syst, toa_error_arb):
    """
    Measure the Time of Arrival (TOA) of a detected pulse.
    
    :param true_toa: True TOA of the pulse
    :param r: Distance between radar and sensor
    :param t: Current time
    :param toa_error_syst: Function to generate systematic error
    :param toa_error_arb: Function to generate arbitrary error
    :return: Measured TOA
    """
    c = 299792458 * ureg.meter / ureg.second  # Speed of light
    delta_Tr = r / c
    TOA_syst = toa_error_syst(t)
    TOA_arb = toa_error_arb(1)[0]  # Generate a single random error
    
    measured_toa = true_toa + delta_Tr + TOA_syst + TOA_arb
    return measured_toa.to(ureg.second)

def measure_frequency(true_frequency, t, frequency_error_syst, frequency_error_arb):
    """
    Measure the frequency of a detected pulse.
    
    :param true_frequency: True frequency of the pulse
    :param t: Current time
    :param frequency_error_syst: Function to generate systematic error
    :param frequency_error_arb: Function to generate arbitrary error
    :return: Measured frequency
    """
    f_syst = frequency_error_syst(t)
    f_arb = frequency_error_arb(1)[0]  # Generate a single random error
    
    measured_frequency = true_frequency + f_syst + f_arb
    return measured_frequency.to(ureg.Hz)

def measure_pulse_width(true_pw, t, pw_error_syst, pw_error_arb):
    """
    Measure the pulse width of a detected pulse.
    
    :param true_pw: True pulse width
    :param t: Current time
    :param pw_error_syst: Function to generate systematic error
    :param pw_error_arb: Function to generate arbitrary error
    :return: Measured pulse width
    """
    PW_syst = pw_error_syst(t)
    PW_arb = pw_error_arb(1)[0]  # Generate a single random error
    
    measured_pw = true_pw + PW_syst + PW_arb
    return measured_pw.to(ureg.second)

def measure_aoa(true_aoa, t, aoa_error_syst, aoa_error_arb):
    """
    Measure the Angle of Arrival (AOA) of a detected pulse.
    
    :param true_aoa: True AOA of the pulse
    :param t: Current time
    :param aoa_error_syst: Function to generate systematic error
    :param aoa_error_arb: Function to generate arbitrary error
    :return: Measured AOA
    """
    AOA_syst = aoa_error_syst(t)
    AOA_arb = aoa_error_arb(1)[0]  # Generate a single random error
    
    measured_aoa = true_aoa + AOA_syst + AOA_arb
    return measured_aoa.to(ureg.degree)

# Additional function for AOA sinusoidal error
def aoa_sinusoidal_error(AOA, A, f, AOA_ref):
    """
    Calculate AOA error with sinusoidal dependency on the direction.
    
    :param AOA: Angle of Arrival
    :param A: Error amplitude
    :param f: Number of sinus periods per 360 degrees
    :param AOA_ref: Reference angle where error is zero
    :return: AOA error
    """
    return A * np.sin(f * (AOA - AOA_ref))