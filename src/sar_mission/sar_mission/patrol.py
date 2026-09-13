"""Nav2 waypoint patrol with explicit failure reporting and real run evidence."""
import json
import time
import signal
from pathlib import Path
import math
import yaml
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

def main(args=None):
    rclpy.init(args=args);nav=BasicNavigator()
    node=nav.getNode() if hasattr(nav,'getNode') else getattr(nav,'node',nav)
    node.declare_parameter('waypoints_file','/ws/install/sar_bringup/share/sar_bringup/config/waypoints.yaml')
    node.declare_parameter('goal_timeout_seconds',300.)
    route=yaml.safe_load(Path(node.get_parameter('waypoints_file').value).read_text())['waypoints']
    record={'source':'nav2_action_results','status':'starting','waypoints':[]}
    path=Path('/ws/results/mission_status.json');path.parent.mkdir(parents=True,exist_ok=True)
    def save():
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(path)
    save()
    try:
        initial=PoseStamped();initial.header.frame_id='map'
        initial.header.stamp=node.get_clock().now().to_msg();initial.pose.orientation.w=1.0
        nav.setInitialPose(initial)
        def startup_timeout(signum,frame):
            raise TimeoutError('Nav2/AMCL did not become active within 180 wall seconds')
        signal.signal(signal.SIGALRM,startup_timeout)
        signal.alarm(180)
        try:nav.waitUntilNav2Active()
        finally:signal.alarm(0)
        record['status']='running';save()
        for i,wp in enumerate(route):
            pose=PoseStamped();pose.header.frame_id='map';pose.header.stamp=node.get_clock().now().to_msg()
            pose.pose.position.x=float(wp['x']);pose.pose.position.y=float(wp['y'])
            pose.pose.orientation.z=math.sin(wp['yaw']/2);pose.pose.orientation.w=math.cos(wp['yaw']/2)
            nav.info(f'Patrol waypoint {i+1}/{len(route)}: {wp}')
            if not nav.goToPose(pose):raise RuntimeError(f'Nav2 rejected waypoint {i+1}')
            start=time.monotonic();timed_out=False
            while not nav.isTaskComplete():
                if time.monotonic()-start>node.get_parameter('goal_timeout_seconds').value:
                    timed_out=True;nav.cancelTask();break
            result=nav.getResult()
            success=result==TaskResult.SUCCEEDED and not timed_out
            record['waypoints'].append({'index':i+1,**wp,'success':success,'result':str(result),'timed_out':timed_out});save()
            if not success:raise RuntimeError(f'Waypoint {i+1} failed: {result}')
            # Hold the final orientation long enough for repeated camera observations.
            start_sim=node.get_clock().now().nanoseconds
            deadline=time.monotonic()+30
            while node.get_clock().now().nanoseconds-start_sim<3e9 and time.monotonic()<deadline:
                rclpy.spin_once(node,timeout_sec=.1)
        record['status']='complete';save();nav.info('All Nav2 patrol waypoints succeeded')
    except (Exception,KeyboardInterrupt) as exc:
        record['status']='failed';record['error']=str(exc);save();nav.error(str(exc));raise
    finally:
        if hasattr(nav,'destroyNode'):nav.destroyNode()
        elif hasattr(node,'destroy_node'):node.destroy_node()
        rclpy.try_shutdown()
