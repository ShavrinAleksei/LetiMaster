from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim',
            output='screen'
        ),
        
        ExecuteProcess(
            cmd=[
                'ros2 service call /spawn turtlesim/srv/Spawn "{x: 2.0, y: 2.0, theta: 0.0, name: \'turtle2\'}"'
            ],
            shell=True,
            output='screen'
        ),
        
        Node(
            package='stalker',
            executable='stalker_node',
            name='stalker_2',
            parameters=[{
                'stalker_name': 'turtle2',
                'victim_name': 'turtle1',
                'speed': 0.7
            }],
            output='screen'
        ),

        ExecuteProcess(
            cmd=[
                'ros2 service call /spawn turtlesim/srv/Spawn "{x: 0.0, y: 0.0, theta: 0.0, name: \'turtle3\'}"'
            ],
            shell=True,
            output='screen'
        ),
                
        Node(
            package='stalker',
            executable='stalker_node',
            name='stalker_3',
            parameters=[{
                'stalker_name': 'turtle3',
                'victim_name': 'turtle2',
                'speed': 0.5
            }],
            output='screen'
        ),
    ])