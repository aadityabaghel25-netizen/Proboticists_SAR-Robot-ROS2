"""Record hashes of the map immediately after a successful live SLAM survey."""
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
root=Path('/ws')
survey=json.loads((root/'results/slam_survey.json').read_text())
if survey.get('status')!='complete':raise SystemExit('Live survey has not completed')
paths=['maps/building.yaml','maps/building.pgm']
record={'source':'slam_toolbox_and_nav2_map_saver','saved_at_utc':datetime.now(timezone.utc).isoformat(),'files':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}}
(root/'maps/slam_provenance.json').write_text(json.dumps(record,indent=2)+'\n')
