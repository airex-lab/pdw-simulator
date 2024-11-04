import streamlit as st
import yaml
import subprocess
import os
import ast
import pandas as pd

def load_config():
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
    else:
        config = {}
    return config

def save_config(config):
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file)

def run_simulation():
    # Ensure main.py is executable and in the same directory
    if os.path.exists('main.py'):
        # Run main.py and capture the output
        subprocess.run(['python', 'main.py'])
    else:
        st.error("main.py not found in the current directory.")

def display_output():
    st.subheader("Simulation Output Log")
    if os.path.exists('output.txt'):
        with open('output.txt', 'r') as f:
            output = f.read()
        st.text_area("Output.txt", output, height=400)
    else:
        st.error("Output.txt not found.")

    st.subheader("PDW Data")
    if os.path.exists('pdw_output.csv'):
        pdw_data = pd.read_csv('pdw_output.csv')
        st.dataframe(pdw_data)
    else:
        st.error("pdw_output.csv not found.")

def main():
    st.set_page_config(page_title="Radar Simulation", layout="wide")
    st.title("Radar Simulation Configuration")

    if 'page' not in st.session_state:
        st.session_state.page = 0
        st.session_state.config = load_config()
        st.session_state.num_radars = 0
        st.session_state.radars_configured = 0

    if st.session_state.page == 0:
        st.header("Select Number of Radars")
        num_radars = st.number_input('Number of Radars', min_value=1, max_value=10, value=2, step=1)
        if st.button("Next"):
            st.session_state.num_radars = num_radars
            st.session_state.config['radars'] = st.session_state.config.get('radars', [])[:num_radars]
            st.session_state.page = 1

    elif st.session_state.page <= st.session_state.num_radars:
        radar_index = st.session_state.page - 1
        radars = st.session_state.config.get('radars', [])
        if len(radars) <= radar_index:
            radars.append({'name': f'Radar{st.session_state.page}'})
            st.session_state.config['radars'] = radars

        radar = radars[radar_index]
        st.header(f"Configure {radar.get('name', f'Radar{st.session_state.page}')}")

        radar['name'] = st.text_input('Radar Name', value=radar.get('name', f'Radar{st.session_state.page}'))
        start_position_str = st.text_input(
            "Start Position (x, y in meters)",
            value=str(radar.get('start_position', [0, 0]))
        )
        try:
            radar['start_position'] = ast.literal_eval(start_position_str)
        except:
            st.error("Invalid format for Start Position. Please enter a list like [x, y].")

        velocity_str = st.text_input(
            "Velocity (vx, vy in m/s)",
            value=str(radar.get('velocity', [0, 0]))
        )
        try:
            radar['velocity'] = ast.literal_eval(velocity_str)
        except:
            st.error("Invalid format for Velocity. Please enter a list like [vx, vy].")

        radar['start_time'] = st.number_input("Start Time (s)", value=float(radar.get('start_time', 0.0)))
        radar['power'] = st.number_input("Power (W)", value=float(radar.get('power', 1000.0)))

        # Rotation Type
        rotation_types = ['constant', 'variable']
        rotation_type_default = radar.get('rotation_type', 'constant')
        if rotation_type_default not in rotation_types:
            rotation_type_default = 'constant'
        radar['rotation_type'] = st.selectbox("Rotation Type", rotation_types, index=rotation_types.index(rotation_type_default))
        radar['rotation_params'] = radar.get('rotation_params', {})
        radar['rotation_params']['t0'] = st.number_input("Rotation t0", value=float(radar['rotation_params'].get('t0', 0.0)))
        radar['rotation_params']['alpha0'] = st.number_input("Initial Angle (rad)", value=float(radar['rotation_params'].get('alpha0', 0.0)))
        radar['rotation_params']['T_rot'] = st.number_input("Rotation Period (s)", value=float(radar['rotation_params'].get('T_rot', 2.5)))

        # PRI Type
        pri_types = ['fixed', 'stagger', 'jitter']
        pri_type_default = radar.get('pri_type', 'fixed')
        if pri_type_default not in pri_types:
            pri_type_default = 'fixed'
        radar['pri_type'] = st.selectbox("PRI Type", pri_types, index=pri_types.index(pri_type_default))
        radar['pri_params'] = radar.get('pri_params', {})
        if radar['pri_type'] == 'fixed':
            radar['pri_params']['pri'] = st.number_input("PRI (s)", value=float(radar['pri_params'].get('pri', 0.001)))
        elif radar['pri_type'] == 'stagger':
            pri_pattern_str = st.text_input("PRI Pattern (s)", value=str(radar['pri_params'].get('pri_pattern', [0.001])))
            try:
                radar['pri_params']['pri_pattern'] = ast.literal_eval(pri_pattern_str)
            except:
                st.error("Invalid format for PRI Pattern. Please enter a list like [0.001, 0.0012, 0.0011].")
        elif radar['pri_type'] == 'jitter':
            radar['pri_params']['mean_pri'] = st.number_input("Mean PRI (s)", value=float(radar['pri_params'].get('mean_pri', 0.001)))
            radar['pri_params']['jitter_percentage'] = st.number_input("Jitter Percentage (%)", value=float(radar['pri_params'].get('jitter_percentage', 5.0)))

        # Frequency Type
        frequency_types = ['fixed', 'hopping']
        frequency_type_default = radar.get('frequency_type', 'fixed')
        if frequency_type_default not in frequency_types:
            frequency_type_default = 'fixed'
        radar['frequency_type'] = st.selectbox("Frequency Type", frequency_types, index=frequency_types.index(frequency_type_default))
        radar['frequency_params'] = radar.get('frequency_params', {})
        frequency_default = radar['frequency_params'].get('frequency', 15e9)
        radar['frequency_params']['frequency'] = st.number_input(
            "Frequency (Hz)", 
            value=float(frequency_default)
        )

        # Pulse Width Type
        pulse_width_types = ['fixed', 'jitter']
        pulse_width_type_default = radar.get('pulse_width_type', 'fixed')
        if pulse_width_type_default not in pulse_width_types:
            pulse_width_type_default = 'fixed'
        radar['pulse_width_type'] = st.selectbox("Pulse Width Type", pulse_width_types, index=pulse_width_types.index(pulse_width_type_default))
        radar['pulse_width_params'] = radar.get('pulse_width_params', {})
        if radar['pulse_width_type'] == 'fixed':
            radar['pulse_width_params']['pulse_width'] = st.number_input("Pulse Width (s)", value=float(radar['pulse_width_params'].get('pulse_width', 1e-6)))
        elif radar['pulse_width_type'] == 'jitter':
            radar['pulse_width_params']['mean_pulse_width'] = st.number_input("Mean Pulse Width (s)", value=float(radar['pulse_width_params'].get('mean_pulse_width', 1e-6)))
            radar['pulse_width_params']['jitter_percentage'] = st.number_input("Jitter Percentage (%)", value=float(radar['pulse_width_params'].get('jitter_percentage', 5.0)))

        # Lobe Pattern
        radar['lobe_pattern'] = radar.get('lobe_pattern', {})
        radar['lobe_pattern']['type'] = st.selectbox("Lobe Pattern Type", ['Sinc'], index=0)
        radar['lobe_pattern']['main_lobe_opening_angle'] = st.number_input("Main Lobe Opening Angle (deg)", value=float(radar['lobe_pattern'].get('main_lobe_opening_angle', 5.0)))
        radar['lobe_pattern']['radar_power_at_main_lobe'] = st.number_input("Radar Power at Main Lobe (dB)", value=float(radar['lobe_pattern'].get('radar_power_at_main_lobe', 0.0)))
        radar['lobe_pattern']['radar_power_at_back_lobe'] = st.number_input("Radar Power at Back Lobe (dB)", value=float(radar['lobe_pattern'].get('radar_power_at_back_lobe', -20.0)))

        if st.button("Next"):
            st.session_state.page += 1

    elif st.session_state.page == st.session_state.num_radars + 1:
        st.header("Configuration Complete")
        if st.button("Generate Data"):
            # Save the updated config
            save_config(st.session_state.config)
            # Run the simulation
            run_simulation()
            # Display the output
            st.session_state.page += 1

    elif st.session_state.page == st.session_state.num_radars + 2:
        st.header("Simulation Output")
        display_output()

    # Option to go back to the start
    if st.button("Restart"):
        st.session_state.page = 0

if __name__ == "__main__":
    main()
