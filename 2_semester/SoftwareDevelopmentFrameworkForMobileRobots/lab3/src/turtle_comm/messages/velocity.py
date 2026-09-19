class VelocityMessage:
    def __init__(self, linear: float = 0.0, angular: float = 0.0):
        self.linear = linear
        self.angular = angular

    def to_dict(self):
        return {"linear": self.linear, "angular": self.angular}

    @classmethod
    def from_dict(cls, data):
        return cls(data.get("linear", 0.0), data.get("angular", 0.0))
    
    def __repr__(self):
        return f"VelocityMessage(linear={self.linear:.2f}, angular={self.angular:.2f})"