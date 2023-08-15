import concurrent.futures
import requests
import json
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

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(ping_device, ip): ip for ip in device_ips}
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            try:
                data = future.result()
                if data:
                    responses.append(data)
            except Exception as exc:
                print(f"Error retrieving data from {ip}: {exc}")

    return [json.loads(item) for item in responses]


def ping_device(ip):
    try:
        url = "http://" + ip
        content = requests.get(url=url, timeout=2).content
        if content:
            data = json.loads(content)
            data["ip"] = ip
            data = json.dumps(data)
            return data
    except Exception:
        return None
