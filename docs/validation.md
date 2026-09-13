# Validation status - 10 September 2026

## Passed

- 11 local unit/static checks: camera tangent geometry, invalid measurements,
  spatial deduplication, source ID association, observation confirmation,
  package data files, Python/XML/YAML parsing, sensor-to-URDF frame consistency,
  world target count and pinned upstream asset hashes.
- Deterministic generated-asset comparison.
- Shell syntax for entrypoint and run scripts.
- Docker Compose configuration validation.
- Gazebo SDF parser accepted both the generated building world and Waffle model.
- Two-page design PDF rendered and visually checked.

These checks do not establish successful navigation or perception in simulation.

## Build attempts and exact blockers

1. Native ARM build failed because required Gazebo Classic/ROS Gazebo packages
   were unavailable from the configured Jammy repositories. Dockerfile and Compose
   now explicitly select Linux amd64.
2. The amd64 build failed while committing a downloaded image layer with
   `input/output error`. The Mac had approximately 1.5 GB free then, and about
   4.8 GB at the last check. Free roughly 20 GB before retrying.
3. Some project files are offloaded to iCloud (`compressed,dataless`). Docker bind
   reads have failed with `Resource deadlock avoided`; host reads have sometimes
   failed with `Operation canceled`. Keep the project downloaded locally or copy
   it to a non-iCloud folder before building.
4. An existing `agviitkgp/task:24` image contains ROS1 Noetic, so it cannot validate
   the required ROS2 Humble interfaces. It has not been deleted or modified.

## Not yet verified

- Complete Docker image and colcon compilation against ROS2 Humble.
- Gazebo startup, sensor messages, TF timing and software camera rendering.
- A completed SLAM survey and saved map.
- AMCL/Nav2 startup and eight successful navigation action results.
- Four correctly localized live detections, RViz output and final results.
- Demo recording, public repository and Drive submission links.

## Resume commands

After freeing space and keeping files local:

```bash
docker compose build
bash tools/run_slam.sh
bash tools/run_mission.sh
# In a second terminal, once the patrol finishes:
docker compose exec sar ros-exec ros2 service call /victim_registry sar_interfaces/srv/GetVictims '{}'
docker compose exec sar python3 /ws/tools/verify_run.py
```

The verifier deliberately fails if evidence is missing. No successful-run
`victims.json` or `verification.json` has been fabricated.
