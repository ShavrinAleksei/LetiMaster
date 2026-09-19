class PoseMessage:
    def __init__(self, x=0.0, y=0.0, theta=0.0):
        self.x = x
        self.y = y
        self.theta = theta

    def to_dict(self):
        return {"x": self.x, "y": self.y, "theta": self.theta}

    @classmethod
    def from_dict(cls, data):
        return cls(data["x"], data["y"], data["theta"])

    def __repr__(self):
        return f"PoseMessage(x={self.x:.2f}, y={self.y:.2f}, theta={self.theta:.2f})"