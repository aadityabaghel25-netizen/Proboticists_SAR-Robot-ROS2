import argparse
import rclpy
from rclpy.node import Node
from sar_interfaces.srv import GetVictims
from sar_mission.result_io import write_results

def main(args=None):
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='/ws/results/victims.json');opts=parser.parse_args(args)
    rclpy.init();node=Node('export_results');client=node.create_client(GetVictims,'/victim_registry')
    try:
        if not client.wait_for_service(timeout_sec=20):raise RuntimeError('Victim registry unavailable after 20 seconds')
        future=client.call_async(GetVictims.Request());rclpy.spin_until_future_complete(node,future,timeout_sec=10)
        if not future.done() or future.result() is None:raise RuntimeError('Registry response timed out or failed')
        response=future.result()
        if not response.success:raise RuntimeError(response.message)
        write_results(opts.output,response.victims)
        node.get_logger().info(f'Exported {len(response.victims)} victims to JSON and CSV')
    finally:node.destroy_node();rclpy.try_shutdown()
