"""Setup-only odometry survey; the scored mission navigates through Nav2."""
import math
import time
import json
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan


def wrap(a):return math.atan2(math.sin(a),math.cos(a))

class Survey(Node):
    def __init__(self):
        super().__init__('slam_survey');self.pose=None;self.scan=None;self.last_odom=0.;self.last_scan=0.
        self.pub=self.create_publisher(Twist,'/cmd_vel',10)
        self.create_subscription(Odometry,'/odom',self.odom,qos_profile_sensor_data)
        self.create_subscription(LaserScan,'/scan',self.laser,qos_profile_sensor_data)
    def odom(self,msg):
        q=msg.pose.pose.orientation;p=msg.pose.pose.position
        self.pose=(p.x,p.y,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)));self.last_odom=time.monotonic()
    def laser(self,msg):self.scan=msg;self.last_scan=time.monotonic()
    def step(self):rclpy.spin_once(self,timeout_sec=.05)
    def stop(self):self.pub.publish(Twist())
    def ready(self):
        end=time.monotonic()+120
        while self.pose is None or self.scan is None:
            if time.monotonic()>end:raise RuntimeError('No odometry/laser scan within 120 seconds')
            self.step()
    def fresh(self):
        if time.monotonic()-min(self.last_odom,self.last_scan)>5:
            self.stop();raise RuntimeError('Stale odometry or laser scan')
    def rotate(self,target):
        end=time.monotonic()+180
        while rclpy.ok():
            self.step();self.fresh();error=wrap(target-self.pose[2])
            if abs(error)<.035:break
            if time.monotonic()>end:raise RuntimeError('Survey rotation timed out')
            cmd=Twist();cmd.angular.z=max(-.45,min(.45,1.5*error));self.pub.publish(cmd)
        self.stop()
    def move(self,x,y):
        self.rotate(math.atan2(y-self.pose[1],x-self.pose[0]));end=time.monotonic()+300
        while rclpy.ok():
            self.step();self.fresh();dx=x-self.pose[0];dy=y-self.pose[1];distance=math.hypot(dx,dy)
            if distance<.1:break
            if time.monotonic()>end:raise RuntimeError('Survey move timed out')
            angle=wrap(math.atan2(dy,dx)-self.pose[2]);cmd=Twist();cmd.angular.z=max(-.5,min(.5,1.5*angle))
            front=[v for i,v in enumerate(self.scan.ranges) if abs(wrap(self.scan.angle_min+i*self.scan.angle_increment))<.35 and math.isfinite(v) and v>=self.scan.range_min]
            if min(front,default=99)<.4:raise RuntimeError('Obstacle blocks setup survey')
            cmd.linear.x=min(.17,.7*distance) if abs(angle)<.35 else 0.;self.pub.publish(cmd)
        self.stop()
    def run(self):
        self.ready();route=[(1.8,1.8),(0,0),(-1.8,1.8),(0,0),(-1.8,-1.8),(0,0),(1.8,-1.8),(0,0)]
        for i,(x,y) in enumerate(route):
            self.get_logger().info(f'SLAM survey {i+1}/{len(route)}');self.move(x,y)
            if x!=0:
                start=self.pose[2]
                for delta in [math.pi/2,math.pi,3*math.pi/2,2*math.pi]:self.rotate(wrap(start+delta))
        self.rotate(0.)
        path=Path('/ws/results/slam_survey.json');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'source':'live_odometry_survey','status':'complete','stops':len(route),'final_odom':self.pose},indent=2)+'\n')

def main(args=None):
    rclpy.init(args=args);node=Survey()
    try:node.run()
    finally:node.stop();node.destroy_node();rclpy.try_shutdown()
