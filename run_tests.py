#!/usr/bin/env python3
"""Main testing script"""

import argparse
import subprocess
import sys
import time
from typing import List, Optional

import psutil

_SIM_TIME_CMD = ["rosparam", "set", "/use_sim_time", "true"]
_LASER_PARAM_CMD = []
_MAP_SERVER_CMD = ["rosrun", "map_server", "map_server", "map/lab.yaml"]

_TO_KILL = []  # type: List[psutil.Process]


def _setup_environment():
    """Run various commands to set up environment"""
    global _TO_KILL
    subprocess.check_call(_SIM_TIME_CMD)
    quickmcl_path = subprocess.check_output(["rospack", "find", "quickmcl"]).decode('utf-8').strip()  # type: str
    subprocess.check_call(["rosparam", "load", "%s/filters/laser_config.yaml" % quickmcl_path,
                           "/scan_to_cloud_filter_chain"])
    _TO_KILL.append(psutil.Popen(_MAP_SERVER_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    time.sleep(1)


def _teardown_environment():
    for proc in _TO_KILL:
        proc.terminate()


def _make_quickmcl_commands(particle_count: int,
                            num_beams: int = 30,
                            publish_cloud: bool = False,
                            internal_laser_processing: bool = True,
                            quickmcl_path: Optional[str] = None,
                            scan_to_cloud_path: Optional[str] = None,
                            **kwargs) -> List[List[str]]:
    cmds = [
        [scan_to_cloud_path, "_high_fidelity:=false", "_target_frame:=base_link",
         "cloud_filtered:=cloud"] if scan_to_cloud_path is not None else None,
        [quickmcl_path, "_publish_particles:=" + ("true" if publish_cloud else "false"),
         "_particle_filter_particle_count_min:=%d" % particle_count,
         "_particle_filter_particle_count_max:=%d" % particle_count, "_likelihood_num_beams:=%d" % num_beams,
         "_internal_laser_processing:=" + ("true" if internal_laser_processing else "false")]]
    return list(filter(bool, cmds))


def _make_amcl_commands(particle_count: int, num_beams: int = 30, **kwargs) -> List[List[str]]:
    return [[kwargs['amcl_path'], "_save_pose_rate:=-1.0", "_recovery_alpha_slow:=0.001",
             "_recovery_alpha_fast:=0.1",
             "_use_map_topic:=true", "_min_particles:=%d" % particle_count, "_max_particles:=%d" % particle_count,
             "_gui_publish_rate:=-1.0", "_odom_model_type:=diff-corrected", "_odom_alpha1:=0.05", "_odom_alpha2:=0.1",
             "_odom_alpha3:=0.02", "_odom_alpha4:=0.05", "_laser_max_beams:=%d" % num_beams]]


def run_a_test(monitor_cmd: List[List[str]], factor: int):
    monitored = []
    for cmd in monitor_cmd:
        monitored.append(psutil.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    # Let process settle (load map etc)
    time.sleep(1)
    proc = psutil.Popen(['rosbag', 'play', 'bags/test_drive.bag',
                         '--clock',
                         '--topics', '/tf', '/tf_static', '/scan',
                         '-r', str(factor)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proc.wait()
    time.sleep(0.5)
    results = []
    for monitored_proc in monitored:
        with monitored_proc.oneshot():
            cpu_usage = monitored_proc.cpu_times()
            memory_usage = monitored_proc.memory_full_info()
            results.append((monitored_proc.name(), cpu_usage, memory_usage))
            monitored_proc.terminate()
    return results


def main():
    parser = argparse.ArgumentParser(description="Measure CPU performance of localisation",
                                     epilog="Note! Start roscore before running this and wait for it to settle.")
    parser.add_argument("program_under_test",
                        choices=('amcl', 'quickmcl'),
                        help='Program to test')
    parser.add_argument("--amcl-path",
                        type=str,
                        default=None,
                        help="Full path to AMCL")
    parser.add_argument("--quickmcl-path",
                        type=str,
                        default=None,
                        help="Full path to QuickMCL")
    parser.add_argument("--scan-to-cloud-path",
                        type=str,
                        default=None,
                        help="Full path to scan_to_cloud_filter_chain")
    parser.add_argument('-s', '--speedup-factor',
                        type=int,
                        default=10,
                        help='Speed up factor for bag playing')
    parser.add_argument('-p', '--particle-count',
                        type=int,
                        default=5000,
                        help='Particle count')
    parser.add_argument('--quickmcl-external-laser',
                        action='store_true',
                        default=False,
                        help="Use external laser processing for QuickMCL.")
    parser.add_argument('-c', '--publish-cloud',
                        action='store_true',
                        default=False,
                        help='Publish particle cloud?')
    parser.add_argument('-b', '--beam-count',
                        type=int,
                        default=30,
                        help='Beam count')
    parser.add_argument('-r', '--repeats',
                        type=int,
                        default=5,
                        help='Number of times to repeat test')
    args = parser.parse_args()

    _setup_environment()

    if args.program_under_test == 'amcl':
        cmd_factory = _make_amcl_commands
    elif args.program_under_test == 'quickmcl':
        cmd_factory = _make_quickmcl_commands
    else:
        raise Exception("Unexpected program under test")
    cmd = cmd_factory(particle_count=args.particle_count,
                      num_beams=args.beam_count,
                      publish_cloud=args.publish_cloud,
                      scan_to_cloud_path=args.scan_to_cloud_path,
                      amcl_path=args.amcl_path,
                      quickmcl_path=args.quickmcl_path,
                      internal_laser_processing=not args.quickmcl_external_laser)
    print("Trial,program,user,sys,uss,Publish cloud,Particle count,Beam count")
    for r in range(args.repeats):
        results = run_a_test(cmd, args.speedup_factor)
        for program, cpu, mem in results:
            print("{trial},{program},{user:.2f},{sys:.2f},{uss},{publish_cloud},{particles},{beams}".format(
                user=cpu.user + cpu.children_user,
                sys=cpu.system + cpu.children_system,
                uss=mem.uss,
                publish_cloud=args.publish_cloud,
                particles=args.particle_count,
                beams=args.beam_count,
                program=program,
                trial=r,
            ))

    _teardown_environment()


if __name__ == '__main__':
    main()
