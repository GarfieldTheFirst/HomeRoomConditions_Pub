import subprocess
import os
import platform
import threading
import requests
import json
import tempfile
import queue
from app import settings_data


def get_discovered_devices_list():
    responses = []
    device_ips = []
    devices = []
    if platform.system() == "Linux":
        # execute command to get all devices in linux
        with tempfile.TemporaryFile() as tempf:
            proc = subprocess.Popen(["ip", "neigh", "show"],
                                    stdout=tempf)
            proc.wait()
            tempf.seek(0)
            devices = list(map(lambda x: x.decode("utf-8"), tempf.readlines()))
    else:
        devices = os.popen('arp -a')
    for device in devices:
        for item in device.split(" "):
            ip_candidate = item.split(".")
            if ip_candidate != '' \
                    and len(ip_candidate) == 4 \
                    and len(list(filter(lambda x: x.isalpha(),
                                        ip_candidate))) == 0:
                device_ips.append(item)
    # add simulated endpoint:
    device_ips.append("127.0.0.1:" +
                      str(settings_data["simulated device port"]))

    jobs = queue.Queue()
    results = queue.Queue()

    pool = [threading.Thread(
        target=ping_device,
        args=(jobs, results)) for i in range(len(device_ips))]

    for p in pool:
        p.start()

    # Cue the ping processes
    for ip in device_ips:
        jobs.put(ip)
    # add "None" to invoke the stop of the ping mehtod
    for p in pool:
        jobs.put(None)

    for p in pool:
        p.join()

    # collect he results
    while not results.empty():
        data = results.get()
        responses.append(data)

    return [json.loads(item) for item in responses]


def ping_device(job_q: queue.Queue,
                results_q: queue.Queue):
    while True:
        ip = job_q.get()
        if ip is None:
            break  # stop trigger for the process
        try:
            url = "http://" + ip
            data = json.loads(requests.get(url=url, timeout=5).content)
            data["ip"] = ip
            data = json.dumps(data)
            if data:
                results_q.put(data)
        except Exception:
            pass
