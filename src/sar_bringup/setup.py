from pathlib import Path
from setuptools import setup

resources = [('share/ament_index/resource_index/packages', ['resource/sar_bringup']),
             ('share/sar_bringup', ['package.xml'])]
for folder in ['launch', 'worlds', 'config', 'models', 'urdf', 'meshes']:
    for directory in sorted({p.parent for p in Path(folder).rglob('*') if p.is_file()}):
        resources.append(('share/sar_bringup/' + str(directory), [str(p) for p in sorted(directory.iterdir()) if p.is_file()]))
setup(name='sar_bringup', version='0.1.0', packages=['sar_bringup'], data_files=resources)
