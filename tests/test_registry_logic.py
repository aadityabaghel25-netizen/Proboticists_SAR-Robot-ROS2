import math
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src/sar_mission'),str(Path(__file__).resolve().parents[1]/'src/sar_perception')]
from sar_mission.registry_logic import RegistryStore
from sar_perception.geometry import cylinder_point

class RegistryTests(unittest.TestCase):
    def test_anonymous_detections_merge_and_require_confirmation(self):
        r=RegistryStore(radius=.4,min_observations=3)
        r.add(2.,3.);r.add(2.1,3.1)
        self.assertEqual(r.confirmed(),[])
        r.add(1.9,2.9)
        self.assertEqual(len(r.confirmed()),1)
        self.assertAlmostEqual(r.confirmed()[0].x,2.)
        self.assertAlmostEqual(r.confirmed()[0].y,3.)
    def test_distinct_victims_and_source_ids(self):
        r=RegistryStore(min_observations=1)
        r.add(1,1,source_id=5);r.add(3,3,source_id=6)
        r.add(1.05,1.05,source_id=5)
        self.assertEqual(len(r.confirmed()),2)
        self.assertEqual(r.confirmed()[0].count,2)
    def test_invalid_observations_never_enter_registry(self):
        r=RegistryStore()
        for args in [(math.nan,1,1),(1,math.inf,1),(1,2,-1),(1,2,1.2)]:
            with self.assertRaises(ValueError):r.add(*args)
        self.assertEqual(len(r.tracks),0)
    def test_two_ids_near_same_position_merge(self):
        r=RegistryStore(min_observations=1)
        r.add(1,1,source_id=2);r.add(1.1,1.1,source_id=8)
        self.assertEqual(len(r.confirmed()),1)

class CameraGeometryTests(unittest.TestCase):
    def test_exact_tangent_rays_recover_off_axis_cylinder_center(self):
        for x,z in [(0.,1.2),(.5,2.),(-.7,3.)]:
            radius=.13;fx=565.;cx=320.;angle=math.atan2(x,z)
            half=math.asin(radius/math.hypot(x,z))
            left=cx+fx*math.tan(angle-half);right=cx+fx*math.tan(angle+half)
            result=cylinder_point(left,right,240.,fx,fx,cx,240.,radius)
            self.assertAlmostEqual(result[0],x,places=8)
            self.assertAlmostEqual(result[2],z,places=8)
    def test_rejects_zero_focal_length(self):
        with self.assertRaises(ValueError):cylinder_point(10,20,5,0,10,5,5,.13)

if __name__=='__main__':unittest.main()
