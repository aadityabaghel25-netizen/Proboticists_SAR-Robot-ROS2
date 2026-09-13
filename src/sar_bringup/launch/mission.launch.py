"""One entry point for SLAM setup or a saved-map AMCL/Nav2 mission."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch_ros.actions import Node, SetParameter
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_nodes(context):
    share = Path(get_package_share_directory('sar_bringup'))
    nav = Path(get_package_share_directory('nav2_bringup'))
    slam = LaunchConfiguration('slam').perform(context).lower() == 'true'
    map_path = LaunchConfiguration('map').perform(context)
    if not slam and not Path(map_path).is_file():
        raise RuntimeError('Saved SLAM map missing. Run tools/run_slam.sh first; see README.md.')
    def include(path, **kwargs):
        return IncludeLaunchDescription(PythonLaunchDescriptionSource(str(path)), launch_arguments=kwargs.items())
    actions = [
        include(Path(get_package_share_directory('gazebo_ros'))/'launch/gazebo.launch.py',
                world=str(share/'worlds/building.world'), gui=LaunchConfiguration('gui').perform(context), verbose='true'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'use_sim_time': True, 'robot_description': (share/'urdf/waffle.urdf').read_text()}]),
        Node(package='gazebo_ros', executable='spawn_entity.py', output='screen',
             arguments=['-entity', 'waffle', '-file', str(share/'models/waffle/model.sdf'), '-z', '0.01', '-timeout', '120']),
        Node(package='rviz2', executable='rviz2', arguments=['-d', str(share/'config/mission.rviz')],
             parameters=[{'use_sim_time':True}], condition=IfCondition(LaunchConfiguration('rviz'))),
    ]
    if slam:
        actions.append(include(Path(get_package_share_directory('slam_toolbox'))/'launch/online_async_launch.py',
                               use_sim_time='True', slam_params_file=str(share/'config/slam.yaml')))
    else:
        actions.extend([
            include(nav/'launch/bringup_launch.py', map=map_path, use_sim_time='True', autostart='True',
                    use_composition='False', params_file=str(share/'config/nav2_params.yaml')),
            Node(package='sar_mission', executable='registry', output='screen', parameters=[{'use_sim_time':True}]),
            Node(package='sar_perception', executable='detector', output='screen',
                 parameters=[str(share/'config/detection.yaml'), {'use_sim_time':True}]),
            Node(package='sar_mission', executable='patrol', output='screen',
                 parameters=[{'use_sim_time':True, 'waypoints_file':str(share/'config/waypoints.yaml')}],
                 condition=IfCondition(LaunchConfiguration('patrol'))),
        ])
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('slam', default_value='False'),
        DeclareLaunchArgument('map', default_value='/ws/maps/building.yaml'),
        DeclareLaunchArgument('gui', default_value='False'),
        DeclareLaunchArgument('rviz', default_value='True'),
        DeclareLaunchArgument('patrol', default_value='True'),
        SetParameter(name='bond_timeout', value=120.0),
        OpaqueFunction(function=launch_nodes),
    ])
