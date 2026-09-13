#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash
export TURTLEBOT3_MODEL=waffle
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-23}"
export ROS_LOCALHOST_ONLY="${ROS_LOCALHOST_ONLY:-1}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export GAZEBO_MODEL_DATABASE_URI=""
export GAZEBO_MODEL_PATH="/ws/install/sar_bringup/share/sar_bringup/models:${GAZEBO_MODEL_PATH:-}"
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export DISPLAY="${DISPLAY:-:99}"
mkdir -p /ws/maps /ws/results
if [[ "$DISPLAY" == ":99" ]] && ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
  Xvfb :99 -screen 0 1440x900x24 +extension GLX +render -noreset >/tmp/xvfb.log 2>&1 &
  ready=0
  for attempt in {1..300}; do
    if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then ready=1; break; fi
    sleep 0.1
  done
  [[ "$ready" == 1 ]] || { cat /tmp/xvfb.log; exit 1; }
fi
if [[ "${SAR_DESKTOP:-0}" == "1" ]]; then
  fluxbox >/tmp/fluxbox.log 2>&1 &
  x11vnc -display "$DISPLAY" -localhost -forever -shared -nopw -rfbport 5900 >/tmp/vnc.log 2>&1 &
  websockify --web=/usr/share/novnc/ 6080 localhost:5900 >/tmp/novnc.log 2>&1 &
fi
exec "$@"
