from dataclasses import dataclass

Arg_Dict_Type = Dict[str, Tuple[Type[float], Type[float], Type[float]] | Type[float]]

@dataclass
class Property:
    name: str
    args: Arg_Dict_Type

@dataclass
class Material:
    """Definition of a material.

    Attributes:
      name: name of the shape e.g. "box"
      method: method that is called to create a shape instance
      args: mapping of method arguments to expected types
    """

    name: str
    method: Callable
    args: Arg_Dict_Type


PROPERTIES = dict(
    density=Property(
        name="Density",
        args=dict(x0=float, x1=float, y0=float, y1=float, z0=float, z1=float),
    ),
    ball=Shape(
        name="ball",
        method=pygmsh.geo.Geometry.add_ball,
        args=dict(x0=(float, float, float), radius=float),
    ),
)