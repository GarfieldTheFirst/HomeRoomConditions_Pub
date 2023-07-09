import subprocess
import threading
import requests
import json
import tempfile
import queue

with open("./appsettings.json") as f:
    settings_data = json.load(f)
    f.close()


def get_discovered_devices_list():
    responses = []
    device_ips = []
    devices = []
    with tempfile.TemporaryFile() as tempf:
        # execute command to get all devices in linux
        # try with ip n or ip -r n
        proc = subprocess.Popen(["arp", "-a"],
                                stdout=tempf)
        proc.wait()
        tempf.seek(0)
        devices = list(map(lambda x: x.decode("utf-8"), tempf.readlines()))
        # yields str: "<name> (ip.ip.ip.ip) at <mac> [ether] on <lan>"
    for device in devices:
        item = device.split(" ")[1]  # get ip in paretheses
        item = item.replace("(", "")
        ip_candidate = item.replace(")", "")
        ip_candidate_number_blocks = ip_candidate.split(".")
        if ip_candidate_number_blocks != '' \
                and len(ip_candidate_number_blocks) == 4 \
                and len(list(filter(lambda x: x.isalpha(),
                                    ip_candidate_number_blocks))) == 0:
            device_ips.append(ip_candidate)
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
