"""Module for simulation control parameters."""

from .datastore import Datastore

control_datastore: Datastore[str, dict] = Datastore(
    "control",
    dict(
        maximum_time_steps=2000000,
        gravity_x=0.0,
        gravity_y=0.0,
        gravity_z=-9.81,
        time_step=2.45e-9,
        output_frequency=400,
        cell_size=0.002,
        maximum_contacting_couples=10000000,
        buffer_size_nbs=0.0001,
        restart_save_number=100000,
        element_type="Linear",
        generate_output_file_only=False,
        gravity_setting_stage=0.0,
        load_ramping_stage=0.0,
        load_constant_stage=0.0,
        unload_ramping_stage=0.0,
        stand_off_distance=0.0,
        jet_load_ramping=0.0,
        chipping_removal=False,
    ),
)
