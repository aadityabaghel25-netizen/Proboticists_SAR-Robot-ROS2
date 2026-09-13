#!/usr/bin/env python3
"""Generate deterministic simulation assets from hashed ROBOTIS/Nav2 sources."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHARE = ROOT / 'src/sar_bringup'
WALLS = [(-4, 0, .15, 8), (4, 0, .15, 8), (0, -4, 8, .15), (0, 4, 8, .15),
         (0, 2.6, .15, 2.8), (0, -2.6, .15, 2.8), (2.6, 0, 2.8, .15), (-2.6, 0, 2.8, .15)]
TARGETS = [(2.8, 2.8), (-2.8, 2.8), (-2.8, -2.8), (2.8, -2.8)]

def assets():
    for row in json.loads((ROOT/'vendor/manifest.json').read_text()):
        assert hashlib.sha256((ROOT/'vendor'/row['file']).read_bytes()).hexdigest() == row['sha256'], row['file']
    out = {}
    sdf = ET.parse(ROOT/'vendor/waffle.original.sdf')
    model = sdf.getroot().find('model')
    for uri in model.findall('.//mesh/uri'):
        uri.text = uri.text.replace('model://turtlebot3_common/meshes/', 'file:///ws/install/sar_bringup/share/sar_bringup/meshes/')
    sensor = model.find(".//sensor[@name='camera']")
    sensor.find('update_rate').text = '5'
    sensor.find('camera/image/width').text = '640'
    sensor.find('camera/image/height').text = '480'
    sensor.find('camera/clip/far').text = '12'
    plugin = sensor.find('plugin')
    ET.SubElement(plugin, 'camera_name').text = 'camera'
    ET.SubElement(plugin, 'frame_name').text = 'camera_rgb_optical_frame'
    laser = model.find(".//sensor[@type='ray']")
    laser.find('update_rate').text = '10'
    laser.find('ray/range/max').text = '8.0'
    out['src/sar_bringup/models/waffle/model.sdf'] = ET.tostring(sdf.getroot())
    urdf = ET.parse(ROOT/'vendor/waffle.original.urdf').getroot()
    for child in list(urdf):
        if child.tag.startswith('{'): urdf.remove(child)
    raw = ET.tostring(urdf).decode().replace('${namespace}', '').replace('package://turtlebot3_description/', 'package://sar_bringup/')
    out['src/sar_bringup/urdf/waffle.urdf'] = raw.encode()
    for mesh in (ROOT/'vendor/meshes').rglob('*'):
        if mesh.is_file() and not mesh.name.startswith('.'): out['src/sar_bringup/meshes/'+str(mesh.relative_to(ROOT/'vendor/meshes'))] = mesh.read_bytes()
    world = ET.Element('sdf', version='1.6'); w = ET.SubElement(world, 'world', name='rescue_building')
    ET.SubElement(w, 'gravity').text = '0 0 -9.81'
    physics = ET.SubElement(w, 'physics', name='default', type='ode')
    ET.SubElement(physics, 'max_step_size').text = '0.004'
    ET.SubElement(physics, 'real_time_update_rate').text = '250'
    scene = ET.SubElement(w, 'scene'); ET.SubElement(scene, 'ambient').text = '.6 .6 .6 1'
    ET.SubElement(scene, 'shadows').text = 'false'
    light=ET.SubElement(w,'light',name='sun',type='directional')
    ET.SubElement(light,'pose').text='0 0 10 0 0 0'
    ET.SubElement(light,'diffuse').text='.8 .8 .8 1'
    ET.SubElement(light,'direction').text='-.3 -.2 -1'
    def solid(name,x,y,z,kind,size,color):
        m=ET.SubElement(w,'model',name=name); ET.SubElement(m,'static').text='true'
        ET.SubElement(m,'pose').text=f'{x} {y} {z} 0 0 0'; link=ET.SubElement(m,'link',name='body')
        for tag in ['collision','visual']:
            e=ET.SubElement(link,tag,name=tag); geom=ET.SubElement(e,'geometry'); shape=ET.SubElement(geom,kind)
            if kind=='box': ET.SubElement(shape,'size').text=size
            else:
                ET.SubElement(shape,'radius').text='.13'; ET.SubElement(shape,'length').text='.6'
            if tag=='visual':
                mat=ET.SubElement(e,'material'); ET.SubElement(mat,'ambient').text=color; ET.SubElement(mat,'diffuse').text=color
    solid('floor',0,0,-.05,'box','9 9 .1','.65 .65 .65 1')
    for i,(x,y,sx,sy) in enumerate(WALLS): solid(f'wall_{i}',x,y,.65,'box',f'{sx} {sy} 1.3','.8 .82 .85 1')
    for i,(x,y) in enumerate(TARGETS): solid(f'victim_{i+1}',x,y,.3,'cylinder','','1 0 0 1')
    # Asymmetric landmark improves localization in the otherwise symmetric rooms.
    solid('cabinet',-3.5,1.5,.35,'box','.4 .7 .7','.1 .2 .65 1')
    out['src/sar_bringup/worlds/building.world']=ET.tostring(world)
    out['src/sar_bringup/config/ground_truth.json']=json.dumps({'frame':'world','victims':[{'id':i+1,'x':x,'y':y} for i,(x,y) in enumerate(TARGETS)]},indent=2).encode()
    nav=yaml.safe_load((ROOT/'vendor/nav2.original.yaml').read_text())
    amcl=nav['amcl']['ros__parameters']; amcl.update(set_initial_pose=True,initial_pose={'x':0.0,'y':0.0,'z':0.0,'yaw':0.0},update_min_d=.05,update_min_a=.05,laser_max_range=8.0,min_particles=300,max_particles=1000,transform_tolerance=2.0)
    nav['bt_navigator']['ros__parameters'].update(default_server_timeout=60, bt_loop_duration=20)
    for key in ['local_costmap','global_costmap']:
        cost=nav[key][key]['ros__parameters'];cost['robot_radius']=.23;cost['transform_tolerance']=2.0
        cost['inflation_layer']['inflation_radius']=.4
        cost['inflation_layer']['cost_scaling_factor']=4.0
        if 'obstacle_layer' in cost:
            cost['obstacle_layer']['scan'].update(obstacle_max_range=7.5,raytrace_max_range=8.0)
        if 'voxel_layer' in cost:
            cost['voxel_layer']['scan'].update(obstacle_max_range=7.5,raytrace_max_range=8.0)
    ctl=nav['controller_server']['ros__parameters'];ctl['controller_frequency']=10.0
    ctl['progress_checker']['movement_time_allowance']=120.0
    ctl['FollowPath'].update(max_vel_x=.18,max_speed_xy=.18,max_vel_theta=.6,min_speed_theta=0.0,acc_lim_x=.6,decel_lim_x=-.6,acc_lim_theta=1.0,decel_lim_theta=-1.0,sim_time=1.5,transform_tolerance=2.0)
    ctl['general_goal_checker'].update(xy_goal_tolerance=.15,yaw_goal_tolerance=.15)
    nav['velocity_smoother']['ros__parameters'].update(max_velocity=[.18,0.0,.6],min_velocity=[-.18,0.0,-.6],max_accel=[.6,0.0,1.0],max_decel=[-.6,0.0,-1.0])
    nav['behavior_server']['ros__parameters'].update(transform_tolerance=2.0)
    nav['lifecycle_manager_navigation'] = {'ros__parameters': {'bond_timeout': 120.0, 'use_sim_time': True}}
    nav['lifecycle_manager_localization'] = {'ros__parameters': {'bond_timeout': 120.0, 'use_sim_time': True}}
    out['src/sar_bringup/config/nav2_params.yaml']=yaml.safe_dump(nav,sort_keys=False).encode()
    waypoints=[]
    for x,y in [(1.8,1.8),(-1.8,1.8),(-1.8,-1.8),(1.8,-1.8)]:
        waypoints += [{'x':x,'y':y,'yaw':math.atan2(y,x)}, {'x':0.0,'y':0.0,'yaw':math.atan2(-y,-x)}]
    out['src/sar_bringup/config/waypoints.yaml']=yaml.safe_dump({'waypoints':waypoints}).encode()
    fx=640/(2*math.tan(1.02974/2))
    out['src/sar_bringup/config/camera_calibration.yaml']=yaml.safe_dump({'image_width':640,'image_height':480,'camera_name':'camera','camera_matrix':{'rows':3,'cols':3,'data':[fx,0.,320.,0.,fx,240.,0.,0.,1.]},'distortion_model':'plumb_bob','distortion_coefficients':{'rows':1,'cols':5,'data':[0.,0.,0.,0.,0.]},'rectification_matrix':{'rows':3,'cols':3,'data':[1.,0.,0.,0.,1.,0.,0.,0.,1.]},'projection_matrix':{'rows':3,'cols':4,'data':[fx,0.,320.,0.,0.,fx,240.,0.,0.,0.,1.,0.]}}).encode()
    # Reference occupancy is only for comparison. The mission uses SLAM output.
    res=.05;n=180;buf=bytearray([254])*(n*n)
    for row in range(n):
        for col in range(n):
            x=-4.5+(col+.5)*res;y=-4.5+(n-row-.5)*res
            if any(abs(x-wx)<=sx/2 and abs(y-wy)<=sy/2 for wx,wy,sx,sy in WALLS) or any(math.hypot(x-tx,y-ty)<=.13 for tx,ty in TARGETS) or (abs(x+3.5)<=.2 and abs(y-1.5)<=.35):buf[row*n+col]=0
    out['maps/reference.pgm']=f'P5\n{n} {n}\n255\n'.encode()+buf
    out['maps/reference.yaml']=b'image: reference.pgm\nresolution: 0.05\norigin: [-4.5, -4.5, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n'
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    for rel,data in assets().items():
        path=ROOT/rel
        if args.check:
            if not path.exists() or path.read_bytes()!=data: raise SystemExit(f'Generated asset differs: {rel}; run python3 tools/generate_assets.py')
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('Generated assets verified' if args.check else 'Generated simulation assets')
if __name__=='__main__':main()
