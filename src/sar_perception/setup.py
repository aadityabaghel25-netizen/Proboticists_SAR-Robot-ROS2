from setuptools import setup
setup(name='sar_perception',version='0.1.0',packages=['sar_perception'],data_files=[('share/ament_index/resource_index/packages',['resource/sar_perception']),('share/sar_perception',['package.xml'])],entry_points={'console_scripts':['detector=sar_perception.detector:main']})
