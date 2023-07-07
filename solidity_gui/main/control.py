"""Module for simulation control parameters."""

from .datastore import Datastore

control_datastore: Datastore[str, object] = Datastore(
    "control",
    dict(
        num_timesteps=2000000,
        time_step_size=2.45000000000e-09,
        gravity_x=0.0,
        gravity_y=0.0,
        gravity_z=0.0,
    ),
)
