#!/usr/bin/env python3
"""Fail unless the saved evidence is from successful SLAM and Nav2 runs."""
import hashlib
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    provenance=json.loads((ROOT/'maps/slam_provenance.json').read_text())
    assert provenance['source']=='slam_toolbox_and_nav2_map_saver'
    for path,digest in provenance['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest, f'Map changed: {path}'
    mission=json.loads((ROOT/'results/mission_status.json').read_text())
    assert mission['status']=='complete' and len(mission['waypoints'])==8,'Nav2 patrol incomplete'
    assert all(wp['success'] for wp in mission['waypoints'])
    result=json.loads((ROOT/'results/victims.json').read_text())
    assert result['source']=='live_ros_registry' and result['frame']=='map'
    victims=result['victims'];assert len(victims)==4, f'Expected four victims, got {len(victims)}'
    assert len({v['id'] for v in victims})==4
    truth=json.loads((ROOT/'src/sar_bringup/config/ground_truth.json').read_text())['victims']
    errors=[];available=list(victims)
    for target in truth:
        v=min(available,key=lambda v:math.hypot(v['x']-target['x'],v['y']-target['y']))
        error=math.hypot(v['x']-target['x'],v['y']-target['y']);assert error<.5, f'Position error {error:.3f}m exceeds 0.5m'
        errors.append(error);available.remove(v)
    report={'status':'passed','victims':4,'all_nav2_goals_succeeded':True,'position_errors_m':errors,'max_error_m':max(errors)}
    (ROOT/'results/verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
