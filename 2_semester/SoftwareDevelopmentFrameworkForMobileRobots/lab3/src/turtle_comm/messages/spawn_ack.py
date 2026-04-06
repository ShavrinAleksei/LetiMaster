class SpawnAckMessage:
    def __init__(self, name: str, success: bool = True):
        self.name = name
        self.success = success

    def to_dict(self):
        return {"name": self.name, "success": self.success}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data.get("success", True))