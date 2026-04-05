import math

class TurtleController:
    def __init__(self, speed=1.0):
        self.speed = speed
        self.stop_distance = 0.8

    def compute_velocity(self, current_pose, target_pose):

        dx = target_pose.x - current_pose.x
        dy = target_pose.y - current_pose.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance < self.stop_distance:
            return 0.0, 0.0

        linear_v = self.speed * distance
        
        angle_to_target = math.atan2(dy, dx)
        angle_diff = angle_to_target - current_pose.theta
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
        angular_v = 4.0 * angle_diff
        
        return linear_v, angular_v
