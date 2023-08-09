import threading
import requests
import json
import queue
from app.utilities.getip import get_local_ip

with open("./appsettings.json") as f:
    settings_data = json.load(f)
    f.close()


def get_discovered_devices_list():
    responses = []
    device_ips = []
    local_ip = get_local_ip().split('.')
    local_ip.pop(3)
    network_base_ip = ''
    for item in local_ip:
        network_base_ip += "{}.".format(item)
    device_ips = [network_base_ip + "{}".format(i) for i in range(0, 255)]
    # simulated endpoint on localhost --> wont be found so added explicitly:
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


if __name__ == "__main__":
    device_list = get_discovered_devices_list()
