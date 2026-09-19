from dataclasses import dataclass
from cyclonedds.idl import IdlStruct

@dataclass
class Twist(IdlStruct, typename="Twist"):
    linear_x: float = 0.0
    linear_y: float = 0.0
    linear_z: float = 0.0
    angular_x: float = 0.0
    angular_y: float = 0.0
    angular_z: float = 0.0

@dataclass
class Pose(IdlStruct, typename="Pose"):
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    linear_velocity: float = 0.0
    angular_velocity: float = 0.0
    name: str = ""

@dataclass
class Spawn(IdlStruct, typename="Spawn"):
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0

@dataclass
class Kill(IdlStruct, typename="Kill"):
    name: str = ""