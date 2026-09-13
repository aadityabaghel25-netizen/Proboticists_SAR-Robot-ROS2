#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker-compose run --rm --service-ports sar bash -c '
set -e
ros2 launch sar_bringup mission.launch.py slam:=true rviz:=true > /ws/results/slam.log 2>&1 &
launch_pid=$!
trap "kill $launch_pid 2>/dev/null || true" EXIT
ros2 run sar_mission survey --ros-args -p use_sim_time:=true
ros2 run nav2_map_server map_saver_cli -f /ws/maps/building --ros-args -p use_sim_time:=true -p save_map_timeout:=30.0
python3 /ws/tools/map_provenance.py
'
