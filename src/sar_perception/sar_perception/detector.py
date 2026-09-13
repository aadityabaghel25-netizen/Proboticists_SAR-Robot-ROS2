"""HSV cylinder detection and image-time camera-to-map projection."""
from collections import deque
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PointStamped
from cv_bridge import CvBridge
from tf2_ros import Buffer, TransformListener, TransformException
from tf2_geometry_msgs import do_transform_point
from sar_interfaces.msg import Victim
from sar_perception.geometry import cylinder_point


class Detector(Node):
    def __init__(self):
        super().__init__('detector')
        defaults={'image_topic':'/camera/image_raw','camera_info_topic':'/camera/camera_info',
                  'cylinder_radius_m':.13,'minimum_area_px':100.,'minimum_range_m':.35,'maximum_range_m':5.,
                  'hsv_lower_1':[0,100,60],'hsv_upper_1':[10,255,255],
                  'hsv_lower_2':[170,100,60],'hsv_upper_2':[179,255,255]}
        for key,value in defaults.items(): self.declare_parameter(key,value)
        self.bridge=CvBridge();self.info=None
        self.tf=Buffer();self.listener=TransformListener(self.tf,self)
        self.pub=self.create_publisher(Victim,'/detected_victims',10)
        self.debug=self.create_publisher(Image,'/detections/image',qos_profile_sensor_data)
        self.create_subscription(CameraInfo,self.param('camera_info_topic'),self.on_info,qos_profile_sensor_data)
        self.create_subscription(Image,self.param('image_topic'),self.on_image,qos_profile_sensor_data)
        self.last_warning=-1e9
        self.pending=deque(maxlen=10)
        self.create_timer(.05,self.process_pending)

    def param(self,key): return self.get_parameter(key).value
    def on_info(self,msg): self.info=msg
    def warn(self,message):
        now=self.get_clock().now().nanoseconds/1e9
        if now-self.last_warning>5:
            self.get_logger().warning(message);self.last_warning=now

    def on_image(self,msg):
        self.pending.append(msg)

    def process_pending(self):
        # Give odometry/TF callbacks time to bracket the image timestamp.
        now=self.get_clock().now().nanoseconds
        while self.pending:
            msg=self.pending[0]
            age=(now-Time.from_msg(msg.header.stamp).nanoseconds)/1e9
            if age<.15:return
            self.pending.popleft()
            if age<=2.0:self.process_image(msg)

    def process_image(self,msg):
        if self.info is None: return
        if self.info.header.frame_id!=msg.header.frame_id or self.info.width!=msg.width or self.info.height!=msg.height:
            self.warn('CameraInfo and Image frame/dimensions differ; refusing projection');return
        try: img=self.bridge.imgmsg_to_cv2(msg,'bgr8')
        except Exception as exc: self.warn(f'Image conversion failed: {exc}');return
        hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        mask=cv2.inRange(hsv,np.array(self.param('hsv_lower_1')),np.array(self.param('hsv_upper_1')))
        mask|=cv2.inRange(hsv,np.array(self.param('hsv_lower_2')),np.array(self.param('hsv_upper_2')))
        mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        contours=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
        for contour in contours:
            area=cv2.contourArea(contour)
            if area<self.param('minimum_area_px'): continue
            x,y,w,h=cv2.boundingRect(contour)
            # A clipped silhouette cannot supply both tangent rays.
            if x<=1 or x+w>=msg.width-1 or w<4 or h<w*.7: continue
            try:
                px,py,pz=cylinder_point(x,x+w,y+h/2,self.info.k[0],self.info.k[4],self.info.k[2],self.info.k[5],self.param('cylinder_radius_m'))
                if not self.param('minimum_range_m')<=pz<=self.param('maximum_range_m'): continue
                p=PointStamped();p.header=msg.header;p.point.x=px;p.point.y=py;p.point.z=pz
                transform=self.tf.lookup_transform('map',msg.header.frame_id,Time.from_msg(msg.header.stamp))
                q=do_transform_point(p,transform)
            except (TransformException,ValueError) as exc: self.warn(f'Projection waiting: {exc}');continue
            # Zero means anonymous observation. The registry owns persistent IDs.
            self.pub.publish(Victim(id=0,x=q.point.x,y=q.point.y,confidence=min(1.,area/(w*h))))
            cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.putText(img,f'map ({q.point.x:.2f}, {q.point.y:.2f})',(x,max(18,y-8)),cv2.FONT_HERSHEY_SIMPLEX,.45,(0,255,0),1)
        debug=self.bridge.cv2_to_imgmsg(img,'bgr8');debug.header=msg.header;self.debug.publish(debug)


def main(args=None):
    rclpy.init(args=args);node=Detector()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()
