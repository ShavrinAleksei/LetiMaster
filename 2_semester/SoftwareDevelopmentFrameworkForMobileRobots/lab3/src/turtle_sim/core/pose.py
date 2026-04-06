from dataclasses import dataclass

@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0