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