#!/usr/bin/env python3
import rospy
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from logic import TurtleController

class TurtleRosNode:
    def __init__(self):
    
        self.stalker_name = rospy.get_param('~stalker_name', 'turtle2')
        self.victim_name = rospy.get_param('~victim_name', 'turtle1')
        speed_param = rospy.get_param('~speed', 1.0)

        self.controller = TurtleController(speed=speed_param)
        
        self.current_pose = None
        self.target_pose = None
        
        self.vel_pub = rospy.Publisher(f'/{self.stalker_name}/cmd_vel', Twist, queue_size=10)
        
        rospy.Subscriber(f'/{self.stalker_name}/pose', Pose, self._pose_cb)
        rospy.Subscriber(f'/{self.victim_name}/pose', Pose, self._target_cb)
        
    def _pose_cb(self, msg): self.current_pose = msg
    def _target_cb(self, msg): self.target_pose = msg
    
    def run(self):
        rate = rospy.Rate(20)
        while not rospy.is_shutdown():
            if self.current_pose and self.target_pose:
                lin, ang = self.controller.compute_velocity(self.current_pose, self.target_pose)
                
                msg = Twist()
                msg.linear.x = lin
                msg.angular.z = ang
                self.vel_pub.publish(msg)
            rate.sleep()

if __name__ == '__main__':
    rospy.init_node('stalker', anonymous=True)
    try:
        node = TurtleRosNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
