#!/usr/bin/env python
from __future__ import print_function
import csv
import json
from pprint import pprint
import requests
# turn off warninggs
requests.packages.urllib3.disable_warnings()
import os
import os.path
import logging
from  time import sleep, time
from dnac_config import DNAC, DNAC_USER, DNAC_PASSWORD

from argparse import ArgumentParser
from dnacentersdk import api
from dnacentersdk.exceptions import ApiError

logger = logging.getLogger(__name__)

class TaskTimeoutError(Exception):
    pass

class TaskError(Exception):
    pass

class Task:
    def __init__(self,dnac, taskid):
        self.dnac = dnac
        self.taskid = taskid
    def wait_for_task(self, timeout=10,retry=1):
        start_time = time()
        first = True
        while True:
            result = dnac.task.get_task_by_id(self.taskid)

            if result.response.endTime is not None:
                return result
            else:
                # print a message the first time throu
                if first:
                    logger.debug("Task:{} not complete, waiting {} seconds, polling {}".format(self.taskid, timeout, retry))
                    first = False
                if timeout and (start_time + timeout < time()):
                    raise TaskTimeoutError("Task %s did not complete within the specified timeout "
                                           "(%s seconds)" % (self.taskid, timeout))

                logging.debug("Task=%s has not completed yet. Sleeping %s seconds..." % (self.taskid, retry))
                sleep(retry)
            if result.response.isError == "True":
                raise TaskError("Task {} had error {}".format(self.taskid, result.response.progress))
        return response

class Interface:
    def __init__(self, **kwags):
        pass

def shorten(intname):
    return intname.replace('abitEthernet', '')
class Device:
    def __init__(self, dnac, ip):
        self.dnac = dnac
        self.ip = ip
        self.deviceid = self._get_uuid()
        self.interfacedict = self.get_interfaces()
    def _get_uuid(self):
        try:
            device = self.dnac.devices.get_network_device_by_ip(ip_address=self.ip)
        except ApiError as e:
            if e.status_code == 404:
                print("Device {} not found".format(self.ip))
            else:
                print("Unknown error:{}".format(e))
            return None

        return  device.response.id

    def get_interfaces(self):
        intdict = {}
        interfaces = self.dnac.devices.get_interface_info_by_id(self.deviceid)
        for interface in interfaces.response:
            name  = shorten(interface.portName)
            intdict[name] = {'id': interface.id, 'status': interface.adminStatus}
        return intdict

    def _find_intf(self, name):
        return self.interfacedict.get(name, None)

    def can_changeintf(self, name, status):
        intf = self._find_intf(name)
        if intf is None:
            raise ValueError("Cannot find interface {}".format(name))
        if intf['status'] == status:
            return None
        else:
            return intf['id']

    def display_interfaces(self):
        for intname in self.interfacedict.keys():
            interface = self.interfacedict[intname]
            print("{:15s}{:10s}".format(intname, interface['status']))

def changeintf(dnac, interfaceid, noshut):
    url = "api/v1/interface/{}?deploymentMode=Deploy".format(interfaceid)
    headers = {"content-type": "application/json"}
    status = "UP" if noshut else "DOWN"

    payload = {"adminStatus": status}
    try:
        task = dnac.custom_caller.call_api(method="PUT", resource_path=url,data=json.dumps(payload), headers=headers)
        return Task(dnac, task.response.taskId)
    except requests.exceptions.HTTPError as e:
        print(e.response, e.strerror)
    return None

def parse_intfs(listintf):
    if listintf is None:
        return []
    else:
        return listintf.split(",")
def change_list(dnac, device, names, isup):
    operation = "UP" if isup else "DOWN"
    tasks = {}
    namelist = parse_intfs(names)
    for intf in namelist:
        intfid = device.can_changeintf(intf, operation)
        if intfid is None:
            print("Skipping:{} op {}".format(intf, operation))
        else:
            t = changeintf(dnac, intfid,noshut=isup )
            tasks[intf] = t
    return tasks


def poll_tasks(tasks):
    while True:
        remaining = {}
        for intf,t in tasks.items():
            try:
                r= t.wait_for_task(timeout=1,retry=1)
                print(r.response.data.replace("\n",''))
            except TaskTimeoutError as e:
                remaining[intf] = t
        if remaining == {}:
             break
        else:
             tasks = remaining

def do_change(dnac, device, ups, downs):
    uptasks = change_list(dnac,device,ups, isup=True )
    poll_tasks(uptasks)
    downtasks = change_list(dnac, device, downs, isup=False)
    poll_tasks(downtasks)

if __name__ == "__main__":
    parser = ArgumentParser(description='Select options.')
    parser.add_argument( '--deviceip', type=str,
            help='device')
    parser.add_argument('--shut', type=str,
                        help='interfaces to shut. comma separated')

    parser.add_argument('--noshut', type=str,
                        help='interfaces to shut. comma separated')
    parser.add_argument('-v', action='store_true',
                        help="verbose")
    args = parser.parse_args()

    if args.v:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.debug("logging enabled")
    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    dnac = api.DNACenterAPI(base_url='https://{}:443'.format(DNAC),
                                username=DNAC_USER,password=DNAC_PASSWORD,verify=False)

    device = Device(dnac, args.deviceip)
    if args.shut is None and args.noshut is None:
        device.display_interfaces()
    else:
        do_change(dnac, device,  args.noshut, args.shut)