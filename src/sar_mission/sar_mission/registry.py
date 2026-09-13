import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from visualization_msgs.msg import Marker, MarkerArray
from sar_interfaces.msg import Victim
from sar_interfaces.srv import GetVictims
from sar_mission.registry_logic import RegistryStore
from sar_mission.result_io import write_results

class Registry(Node):
    def __init__(self):
        super().__init__('victim_registry')
        self.declare_parameter('dedup_radius_m',.45);self.declare_parameter('min_observations',3)
        self.declare_parameter('output','/ws/results/victims.json')
        self.store=RegistryStore(self.get_parameter('dedup_radius_m').value,self.get_parameter('min_observations').value)
        self.create_subscription(Victim,'/detected_victims',self.add,10)
        self.create_service(GetVictims,'/victim_registry',self.get)
        self.markers=self.create_publisher(MarkerArray,'/victim_markers',QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.timer=self.create_timer(1.,self.publish)
        self.reported=set()

    def add(self,msg):
        try:self.store.add(msg.x,msg.y,msg.confidence,msg.id)
        except ValueError as exc:self.get_logger().warning(str(exc))

    def get(self,request,response):
        response.victims=[Victim(id=t.id,x=t.x,y=t.y,confidence=t.confidence) for t in self.store.confirmed()]
        response.success=True;response.message=f'{len(response.victims)} confirmed victims in map frame'
        return response

    def publish(self):
        tracks=self.store.confirmed();array=MarkerArray()
        for t in tracks:
            for text in [False,True]:
                marker=Marker();marker.header.frame_id='map';marker.header.stamp=self.get_clock().now().to_msg()
                marker.ns='victim_labels' if text else 'victims';marker.id=t.id;marker.action=Marker.ADD
                marker.type=Marker.TEXT_VIEW_FACING if text else Marker.CYLINDER
                marker.pose.position.x=t.x;marker.pose.position.y=t.y;marker.pose.position.z=.85 if text else .3
                marker.pose.orientation.w=1.;marker.scale.x=.26;marker.scale.y=.26;marker.scale.z=.2 if text else .6
                marker.color.r=1.;marker.color.g=1. if text else .1;marker.color.b=1. if text else .1;marker.color.a=.95
                marker.text=f'Victim {t.id} ({t.x:.2f}, {t.y:.2f})';array.markers.append(marker)
            if t.id not in self.reported:
                self.get_logger().info(f'Confirmed victim {t.id}: map ({t.x:.2f}, {t.y:.2f})');self.reported.add(t.id)
        self.markers.publish(array)
        write_results(self.get_parameter('output').value,tracks,simulation_time=self.get_clock().now().nanoseconds/1e9)

def main(args=None):
    rclpy.init(args=args);node=Registry()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()
