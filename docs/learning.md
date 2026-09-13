# Viva and beginner guide

## A simple explanation to say aloud

“My project simulates a rescue robot inside a building. First, the robot uses
laser measurements and SLAM to create a map. During the mission, AMCL estimates
where the robot is on that map, and Nav2 drives it through a list of locations.
The camera finds red cylinders representing victims. Because their size is known,
I can estimate their distance. TF2 converts that position from the camera's view
to the building map. A registry combines repeated sightings of the same victim
and returns the final coordinates.”

Only describe the demonstration as successfully tested after the real-run checks pass.

## Ten likely viva questions

1. **Why Docker?** It packages ROS and its dependencies so the host does not need
   a separate ROS installation.
2. **Why Waffle?** The task requires it, and its simulated RGB camera supports detection.
3. **What is SLAM?** Building a map while estimating the robot's position.
4. **How is AMCL different?** It estimates position on an already saved map.
5. **What does Nav2 do?** It plans a route, avoids obstacles, and commands movement.
6. **How are victims detected?** HSV color thresholding finds red regions; contours
   locate their image boundaries.
7. **How do you get distance from an RGB image?** The cylinder has a known width;
   its apparent angular width and camera calibration determine its range.
8. **What is TF2?** A system for converting positions between coordinate frames
   at a particular time.
9. **How do you avoid counting one victim repeatedly?** Nearby observations update
   one stored centroid. A track needs three observations before confirmation.
10. **What are the main limitations?** Known cylinder size, controlled red objects,
    possible occlusion, and a fixed setup survey route. Real runs must verify accuracy.

## Lesson 1: Linux and Docker

The container runs Ubuntu Linux. A terminal sends commands to that environment.
`Dockerfile` describes installation; `docker-compose.yml` describes how to run it.
`entrypoint.sh` loads ROS and sets `TURTLEBOT3_MODEL=waffle`.

Run `docker compose build`, then the setup/mission scripts from the README.
Expected: the build ends successfully, and runtime logs show nodes starting.
**Quiz:** Why does installing ROS in the container avoid a host ROS installation?

## Lesson 2: Nodes, topics, services and actions

A node is one running program. A topic is a stream, such as `/camera/image_raw`.
A service asks a question and receives a response, such as `/victim_registry`.
An action is a longer task with a result, such as `/navigate_to_pose`.
Launch files start related programs together.

Run `docker compose exec sar ros-exec ros2 node list` and `docker compose exec sar ros-exec ros2 topic list`.
Expected: detector, registry, navigation and sensor names.
**Quiz:** Why is navigation an action rather than a camera-style topic?

## Lesson 3: Gazebo and sensors

Gazebo simulates physics and sensors. `src/sar_bringup/worlds/building.world`
contains rooms and cylinders. `models/waffle/model.sdf` contains robot physics
and sensor plugins; `urdf/waffle.urdf` describes link transforms for ROS.

Run `docker compose exec sar ros-exec ros2 topic hz /scan`.
Expected: repeated LiDAR messages (nominal simulation rate 10 Hz; wall-time rate
can be slower under emulation).
**Quiz:** What is the difference between the world and the robot model?

## Lesson 4: SLAM and map saving

SLAM Toolbox uses scans and movement to construct an occupancy grid: free space,
occupied space, and unknown space. `tools/run_slam.sh` conducts the setup survey
and saves the map image plus YAML metadata.

Run `bash tools/run_slam.sh` with the mission stopped.
Expected: eight survey stops followed by `maps/building.pgm` and `building.yaml`.
**Quiz:** Why isn't a drawing of the building proof that SLAM was run?

## Lesson 5: AMCL

AMCL compares scans to the saved map and maintains candidate robot poses.
It publishes `map -> odom`, connecting local motion estimates to the global map.
The configured starting pose matches the simulation spawn at the centre.

Run `docker compose exec sar ros-exec ros2 lifecycle get /amcl`.
Expected during a working mission: `active`.
**Quiz:** Why should AMCL and SLAM not both publish the same map transform?

## Lesson 6: Nav2 and waypoints

`config/waypoints.yaml` is the route. `sar_mission/patrol.py` sends each goal,
waits for the action result, and records success or failure. Nav2 plans and drives.

Inspect `results/mission_status.json` after a mission.
Expected after success: `status: complete` and eight successful goals.
**Quiz:** Why is reaching all goals stronger evidence than just starting Nav2?

## Lesson 7: Camera and OpenCV

The camera sends pixels; CameraInfo gives focal lengths and image centre.
HSV separates hue from brightness. The detector thresholds red and finds contours.
`geometry.py` converts the known cylinder width into range using tangent rays.

Run `docker compose exec sar ros-exec ros2 topic echo /camera/camera_info --once`.
Expected: 640 by 480 image dimensions and nonzero focal lengths.
**Quiz:** What happens to the range estimate if the real cylinder is twice as wide?

## Lesson 8: TF2

The camera sees a position relative to itself. TF2 converts it through robot and
odometry frames into the map. Image timestamps matter because the robot moves.
The optical frame uses x right, y down, z forward.

Run `docker compose exec sar ros-exec ros2 run tf2_ros tf2_echo map camera_rgb_optical_frame`.
Expected: a changing translation and rotation as the robot moves.
**Quiz:** Why could using a transform from the wrong time move a detected victim?

## Lesson 9: Registry

A victim appears in many frames. `registry_logic.py` associates nearby points,
updates their mean position, and confirms the track after three observations.
IDs represent discovery order because red cylinders do not encode IDs.

Run the `/victim_registry` service command from the README.
Expected after a verified patrol: four victims with unique IDs and map x/y.
**Quiz:** What happens if two different victims are closer than the merge radius?

## Lesson 10: Debugging

Start with evidence: Docker logs, node list, sensor topics, TF, lifecycle state,
and mission status. No image means perception has no input. Missing TF means
projection should wait. No active AMCL means localization has not started.

Run `docker compose logs --tail=100 sar` and the inspection commands in README.
Expected: errors identify the failing component rather than silently claiming success.
**Quiz:** Which three checks would you run if the robot moves but no victims appear?

Work through one lesson at a time and answer its quiz before continuing.
