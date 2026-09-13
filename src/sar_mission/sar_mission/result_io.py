import csv
import json
from pathlib import Path
from datetime import datetime, timezone

def write_results(path,victims,**metadata):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    rows=[{'id':v.id,'x':v.x,'y':v.y,'confidence':v.confidence} for v in victims]
    data={'source':'live_ros_registry','frame':'map','exported_at_utc':datetime.now(timezone.utc).isoformat(),**metadata,'victims':rows}
    tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)
    csv_path=path.with_suffix('.csv');tmp=csv_path.with_suffix('.csv.tmp')
    with tmp.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','x','y','confidence']);writer.writeheader();writer.writerows(rows)
    tmp.replace(csv_path)
