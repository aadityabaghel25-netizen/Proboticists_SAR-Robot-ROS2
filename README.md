# Search-and-Rescue Marker Finder

A Docker-only ROS2 Humble project using Gazebo Classic 11, TurtleBot3 Waffle,
SLAM Toolbox, AMCL, Nav2, OpenCV and TF2. Four red cylinders represent victims
in a four-room building. The camera estimates cylinder range from its known
0.26 m diameter; TF2 projects observations into the map frame; the registry
merges nearby observations and exposes confirmed victims through a service.

**Validation status:** source implementation is present. A successful full Docker
build, live SLAM survey, and Nav2 mission must still be verified. Do not submit
`victims.example.json`, `reference.pgm`, or `legacy-placeholder.pgm` as live evidence.
See [docs/validation.md](docs/validation.md) for the current checks and blockers.

## Requirements

- Docker Desktop running (or Docker Engine + Compose on Linux).
- Internet for the first build; allow roughly 20 GB free disk and 8 GB Docker RAM.
- Linux amd64 is explicitly selected for Gazebo Classic's Ubuntu Jammy packages.
  Apple Silicon uses emulation and will be slower. No host ROS installation is needed.
- On a Mac, keep this folder downloaded locally, rather than offloaded to iCloud.

## Build

From this project folder:

```bash
docker compose build
```

The build validates generated assets, compiles the four ROS packages, and runs
unit tests. Upstream robot meshes and configurations are bundled in `vendor/`;
their commit URLs and SHA256 hashes are in `vendor/manifest.json`. Ubuntu/ROS apt
packages are resolved at build time; the final versions are recorded inside the
image at `/ws/installed-packages.txt`. This is not a bit-for-bit locked apt snapshot.

## Step 1: create the actual SLAM map

```bash
bash tools/run_slam.sh
```

This starts Gazebo and SLAM Toolbox, then drives an odometry-controlled setup
survey through each room, with a full turn at each room stop. LiDAR stops the
survey if an obstacle blocks its route. It saves `maps/building.pgm` and
`maps/building.yaml` with Nav2's map saver, then records their hashes in
`maps/slam_provenance.json`. The log is `results/slam.log`. The survey is only
for map creation; the mission uses Nav2.

View the desktop at http://localhost:6080/vnc.html while the survey runs.
Simulation on an emulated Mac can take substantially longer than real time.

For a manual mapping session instead:

```bash
docker compose run --rm --service-ports --name sar-mapping sar \
  ros2 launch sar_bringup mission.launch.py slam:=true
```

In another terminal:

```bash
docker exec -it sar-mapping bash -lc 'source /opt/ros/humble/setup.bash; source /ws/install/setup.bash; ros2 run teleop_twist_keyboard teleop_twist_keyboard'
docker exec sar-mapping bash -lc 'source /opt/ros/humble/setup.bash; source /ws/install/setup.bash; ros2 run nav2_map_server map_saver_cli -f /ws/maps/building --ros-args -p use_sim_time:=true -p save_map_timeout:=30.0'
```

Manual mapping produces a usable map but does not claim automatic survey evidence.
Use the automatic script for the supplied verification workflow.

## Step 2: AMCL localization and Nav2 patrol

After the setup command has finished:

```bash
bash tools/run_mission.sh
```

Open http://localhost:6080/vnc.html to see RViz. The mission starts the robot
at `(0,0,0)`, matching AMCL's configured initial pose. It navigates to each room,
faces the cylinder, pauses for observations, and returns through the central
opening. `config/waypoints.yaml` supplies all goals. Mission failures are written
to `results/mission_status.json`; they are never reported as successful patrols.

To launch localization and navigation without an automatic patrol:

```bash
docker compose run --rm --service-ports --name sar-manual sar \
  ros2 launch sar_bringup mission.launch.py patrol:=false
```

Run the patrol later (with the normal `sar` service running without a patrol):

```bash
docker compose exec sar ros-exec ros2 run sar_mission patrol --ros-args -p use_sim_time:=true
```

Do not start a second patrol while one is active. A manual Nav2 goal is:

```bash
docker compose exec sar ros-exec ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: map}, pose: {position: {x: 1.8, y: 1.8, z: 0.0}, orientation: {z: 0.382683, w: 0.923880}}}}'
```

When using the `sar-manual` container above, replace `docker compose exec sar`
with `docker exec sar-manual ros-exec` in commands requiring the ROS environment.

## Registry and results

```bash
docker compose exec sar ros-exec ros2 service call /victim_registry sar_interfaces/srv/GetVictims '{}'
docker compose exec sar ros-exec ros2 run sar_mission export_results --output /ws/results/victims.json
docker compose exec sar python3 /ws/tools/verify_run.py
```

The registry continuously writes JSON/CSV and publishes `/victim_markers`.
The verification command requires a real saved map, eight successful Nav2 goals,
four distinct victims, and less than 0.5 m error against the simulation's ground
truth. Ground truth is read only by validation, never by the detector or registry.
A failed or incomplete run exits with an error.

## Inspect and stop

```bash
docker compose exec sar ros-exec ros2 node list
docker compose exec sar ros-exec ros2 topic list
docker compose exec sar ros-exec ros2 topic hz /scan
docker compose exec sar ros-exec ros2 topic hz /camera/image_raw
docker compose exec sar ros-exec ros2 run tf2_ros tf2_echo map camera_rgb_optical_frame
docker compose exec sar ros-exec ros2 lifecycle get /amcl
docker compose logs --tail=100 sar
docker compose down
```

## Development checks

```bash
python3 -m unittest discover -s tests -p test_registry_logic.py -v
# The following also needs PyYAML and setuptools:
python3 tools/generate_assets.py --check
python3 -m unittest discover -s tests -v
```

`python3 tools/generate_assets.py` regenerates the bundled world, robot model,
reference map, camera calibration and navigation configuration from pinned assets.
It never manufactures a SLAM map or live victim results.

## Documentation

- [Design and tradeoffs](docs/design.md)
- [Two-page design PDF](docs/design.pdf)
- [Complete file tree](docs/file-tree.txt)
- [Submission checklist](docs/submission.md)
- [Validation status](docs/validation.md)
- [Viva questions and beginner lessons](docs/learning.md)
- [Recovered specification text](docs/specification-recovered.txt)

The specification also requests a public GitHub link, Google Drive folder, demo
recording, and a 1–2 page design PDF. These are separate submission requirements;
local code creation does not publish anything to your accounts.
