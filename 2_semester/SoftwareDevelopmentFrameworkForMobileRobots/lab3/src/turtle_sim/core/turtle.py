from turtle_sim.core import Pose, Velocity

class Turtle:
    def __init__(self, name: str, pose: Pose = None, velocity: Velocity = None):
        self.name = name
        self.pose = pose if pose else Pose()
        self.velocity = velocity if velocity else Velocity()