class SpawnMessage:
    def __init__(self, name: str, x: float = 0.0, y: float = 0.0, theta: float = 0.0):
        self.name = name
        self.x = x
        self.y = y
        self.theta = theta

    def to_dict(self):
        return {"name": self.name, "x": self.x, "y": self.y, "theta": self.theta}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data.get("x", 0.0), data.get("y", 0.0), data.get("theta", 0.0))