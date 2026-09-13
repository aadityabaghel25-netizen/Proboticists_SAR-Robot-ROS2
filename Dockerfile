FROM --platform=linux/amd64 ros:humble-ros-base-jammy
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive \
    TURTLEBOT3_MODEL=waffle \
    ROS_DOMAIN_ID=23 \
    ROS_LOCALHOST_ONLY=1 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    QT_X11_NO_MITSHM=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    gazebo ros-humble-gazebo-ros-pkgs \
    ros-humble-navigation2 ros-humble-nav2-bringup \
    ros-humble-turtlebot3-gazebo ros-humble-turtlebot3-description ros-humble-turtlebot3-msgs \
    ros-humble-slam-toolbox ros-humble-cv-bridge ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs ros-humble-robot-state-publisher \
    ros-humble-rviz2 ros-humble-rosidl-default-generators \
    ros-humble-rmw-fastrtps-cpp ros-humble-teleop-twist-keyboard \
    python3-opencv python3-numpy python3-yaml python3-pytest \
    python3-colcon-common-extensions build-essential \
    xvfb x11vnc novnc websockify fluxbox xauth x11-utils mesa-utils \
    libgl1-mesa-dri tini procps && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /ws
COPY vendor /ws/vendor
COPY tools /ws/tools
COPY src /ws/src
COPY tests /ws/tests
COPY maps /ws/maps
COPY docs /ws/docs
RUN python3 tools/generate_assets.py --check && \
    source /opt/ros/humble/setup.bash && \
    colcon build --event-handlers console_direct+ && \
    source /ws/install/setup.bash && \
    python3 -m pytest -q tests && \
    colcon test --event-handlers console_direct+ && \
    colcon test-result --verbose && \
    mkdir -p /ws/results && \
    dpkg-query -W > /ws/installed-packages.txt
COPY entrypoint.sh /entrypoint.sh
COPY tools/ros-exec /usr/local/bin/ros-exec
RUN chmod +x /entrypoint.sh /usr/local/bin/ros-exec
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["ros2", "launch", "sar_bringup", "mission.launch.py"]
