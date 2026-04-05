#!/usr/bin/env python3
import rospy
import roslaunch
import os
from roslaunch import rlutil

def launch_chain(num_followers):
    uuid = rlutil.get_or_generate_uuid(None, False)
    roslaunch.configure_logging(uuid)
    
    launch = roslaunch.scriptapi.ROSLaunch()
    launch.start()

    node_sim = roslaunch.core.Node("turtlesim", "turtlesim_node", name="sim")
    process_sim = launch.launch(node_sim)
    
    rospy.sleep(0.5)

    for i in range(2, num_followers + 2):
        if not rospy.is_shutdown():
            stalker = f"turtle{i}"
            victim = f"turtle{i-1}"
        
            os.system(f"rosservice call /spawn {i//11} {i%11} 0.0 '{stalker}'")

            node_stalker = roslaunch.core.Node(
                package="hello_world",
                node_type="ros1.py",
                name=f"stalker_{i}",
                args=f"_stalker_name:={stalker} _victim_name:={victim} _speed:=1.0"
            )
            
            launch.launch(node_stalker)
            rospy.loginfo(f"Запущена нода: {stalker} преследует {victim}")


    try:
        launch.spin()
    finally:
        launch.shutdown()

if __name__ == "__main__":
    try:
        n = int(input("Введите количество черепашек-преследователей: "))
        launch_chain(n)
    except KeyboardInterrupt:
        pass
