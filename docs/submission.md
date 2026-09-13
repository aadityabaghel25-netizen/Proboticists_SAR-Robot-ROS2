# Submission checklist

## Required runtime evidence

- [ ] `docker compose build` completes successfully.
- [ ] `bash tools/run_slam.sh` completes and saves a real static map.
- [ ] `maps/slam_provenance.json` matches the saved map files.
- [ ] `bash tools/run_mission.sh` completes all eight Nav2 goals.
- [ ] RViz shows the robot, LiDAR, navigation path, camera image and four victims.
- [ ] Registry service returns four unique victims in map coordinates.
- [ ] JSON/CSV is exported from this run, not copied from an example.
- [ ] `python3 /ws/tools/verify_run.py` passes inside the mission container.
- [ ] Record the desktop showing patrol, camera detections and registry markers.

## Required deliverables

- [ ] Public GitHub repository with Dockerfile, Compose, packages, launch files,
      parameters, generated world/robot assets, actual saved map and real results.
- [ ] Keep the bundled upstream licenses and manifest in the repository.
- [ ] Google Drive folder containing the demo video and 1–2 page design PDF.
- [ ] Set Drive sharing to “Anyone with the link can view” and verify the link.
- [ ] Submit both repository and Drive links.

Publication and account sharing have not been performed by this local build task.
Do not mark runtime requirements complete based only on unit tests.

## Recording

Open the noVNC desktop at http://localhost:6080/vnc.html. Use macOS screen recording
(Shift-Command-5) or your Linux screen recorder. Start before the patrol, show
RViz while the robot visits rooms, and show the registry service output at the end.
Keep the recording unedited where possible so successful navigation is visible.
