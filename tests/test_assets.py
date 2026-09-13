import ast
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import yaml
ROOT=Path(__file__).resolve().parents[1]

class AssetTests(unittest.TestCase):
    def test_python_xml_yaml_parse(self):
        for file in (ROOT/'src').rglob('*.py'):ast.parse(file.read_text(),filename=str(file))
        for pattern in ['*.xml','*.sdf','*.urdf','*.world']:
            for file in (ROOT/'src').rglob(pattern):ET.parse(file)
        for file in (ROOT/'src').rglob('*.yaml'):self.assertIsInstance(yaml.safe_load(file.read_text()),dict)
    def test_robot_sensor_and_tf_names_match(self):
        root=ET.parse(ROOT/'src/sar_bringup/models/waffle/model.sdf')
        frame=root.find(".//sensor[@name='camera']/plugin/frame_name").text
        urdf=ET.parse(ROOT/'src/sar_bringup/urdf/waffle.urdf')
        self.assertIsNotNone(urdf.find(f".//link[@name='{frame}']"))
        self.assertEqual(root.find(".//sensor[@type='ray']/plugin/frame_name").text,'base_scan')
        self.assertNotIn('${',(ROOT/'src/sar_bringup/urdf/waffle.urdf').read_text())
    def test_world_contains_four_targets_and_walls(self):
        root=ET.parse(ROOT/'src/sar_bringup/worlds/building.world')
        models=root.findall('.//world/model')
        self.assertEqual(sum(m.get('name').startswith('victim_') for m in models),4)
        self.assertEqual(sum(m.get('name').startswith('wall_') for m in models),8)
    def test_vendor_hashes(self):
        for row in json.loads((ROOT/'vendor/manifest.json').read_text()):
            self.assertEqual(hashlib.sha256((ROOT/'vendor'/row['file']).read_bytes()).hexdigest(),row['sha256'])
    def test_all_setup_data_files_exist(self):
        # Capture setup() without importing or installing ROS packages.
        import runpy
        from unittest.mock import patch
        import os
        previous=os.getcwd()
        try:
            for directory in (ROOT/'src').iterdir():
                if not (directory/'setup.py').exists():continue
                os.chdir(directory)
                with patch('setuptools.setup') as setup:
                    runpy.run_path(str(directory/'setup.py'))
                for _,files in setup.call_args.kwargs['data_files']:
                    for file in files:self.assertTrue(Path(file).is_file(),str(directory/file))
        finally:os.chdir(previous)

if __name__=='__main__':unittest.main()
