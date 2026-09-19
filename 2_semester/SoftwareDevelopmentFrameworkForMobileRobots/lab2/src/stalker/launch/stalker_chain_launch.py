from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
import random

def create_stalker_nodes(context):
    num_followers = int(LaunchConfiguration('num_followers').perform(context))
    speed = float(LaunchConfiguration('speed').perform(context))
    
    actions = []
    prev_turtle = 'turtle1'

    for i in range(2, num_followers + 2):
        stalker = f'turtle{i}'
        x = random.uniform(0.0, 11.0)
        y = random.uniform(0.0, 11.0)
        
        actions.append(ExecuteProcess(
            cmd=[
                f'ros2 service call /spawn turtlesim/srv/Spawn "{{x: {x}, y: {y}, theta: 0.0, name: \'{stalker}\'}}"'
            ],
            name=f'spawn_{stalker}',
            shell=True
        ))
        
        actions.append(Node(
            package='stalker',
            executable='stalker_node',
            name=f'stalker_{i}',
            parameters=[{
                'stalker_name': stalker,
                'victim_name': prev_turtle,
                'speed': speed
            }],
            output='screen'
        ))

        prev_turtle = stalker

    return actions      

def generate_launch_description():    
    return  LaunchDescription([
        DeclareLaunchArgument(
            'num_followers',
            default_value='2',
        ),

        DeclareLaunchArgument(
            'speed',
            default_value='0.9',
        ),

        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim',
            output='screen'
        ),

        OpaqueFunction(function=create_stalker_nodes),
    ])