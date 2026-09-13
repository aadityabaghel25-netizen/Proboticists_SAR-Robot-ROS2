#!/usr/bin/env python3
"""Maintainer-only refresh; normal builds use the committed, hashed assets."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen, Request
import ssl

ROOT = Path(__file__).resolve().parents[1]

def get(url):
    # Keep TLS verification enabled; use a Python installation with trusted CAs.
    with urlopen(Request(url, headers={'User-Agent': 'sar-humble-project'}), timeout=60) as response:
        return response.read()

def main():
    repos = {
        'simulation': ('ROBOTIS-GIT/turtlebot3_simulations', 'humble'),
        'description': ('ROBOTIS-GIT/turtlebot3', 'humble'),
        'navigation': ('ros-navigation/navigation2', 'humble'),
    }
    resolved = {k: (repo, json.loads(get(f'https://api.github.com/repos/{repo}/commits/{branch}'))['sha'])
                for k, (repo, branch) in repos.items()}
    files = [
        ('simulation', 'turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf', 'waffle.original.sdf'),
        ('simulation', 'LICENSE', 'TURTLEBOT3_SIMULATIONS_LICENSE'),
        ('description', 'turtlebot3_description/urdf/turtlebot3_waffle.urdf', 'waffle.original.urdf'),
        ('description', 'LICENSE', 'TURTLEBOT3_LICENSE'),
        ('navigation', 'nav2_bringup/params/nav2_params.yaml', 'nav2.original.yaml'),
        ('navigation', 'LICENSE', 'NAV2_LICENSE'),
    ]
    for mesh in ['bases/waffle_base.stl', 'wheels/left_tire.stl', 'wheels/right_tire.stl', 'sensors/lds.stl', 'sensors/r200.dae']:
        files.append(('description', 'turtlebot3_description/meshes/' + mesh, 'meshes/' + mesh))
    manifest = []
    for key, source, dest in files:
        repo, sha = resolved[key]
        url = f'https://raw.githubusercontent.com/{repo}/{sha}/{source}'
        data = get(url)
        path = ROOT / 'vendor' / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        manifest.append({'file': dest, 'url': url, 'sha256': hashlib.sha256(data).hexdigest()})
        print(dest, len(data), flush=True)
    (ROOT / 'vendor/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

if __name__ == '__main__':
    main()
