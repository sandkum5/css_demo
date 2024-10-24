#!/usr/bin/env python3
"""
    Script to get IMM Domain FI Transceiver details
"""

import os
import sys
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv)

def get_token(client_id, client_secret):
    """ Get oAuth Token """
    token_url="https://intersight.com/iam/token"
    client_auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    post_data = {"grant_type": "client_credentials"}
    response = requests.post(url=token_url,
                            auth=client_auth,
                            data=post_data)
    if response.status_code != 200:
        print("Failed to obtain token from the OAuth 2.0 server", file=sys.stderr)
        sys.exit(1)
    token_json = response.json()
    return token_json["access_token"]
    
def get_api_data(token, client_id, client_secret, api_url):
    """ Get API Endpoint Data """
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url=api_url, headers=headers)
    if	response.status_code == 401:
        print("Existing Token Expired. Generating a new one!")
        token = get_token(client_id, client_secret)
        get_api_data(token, client_id, client_secret, api_url)
    else:
        return response.json()

if __name__ == '__main__':
    # Set variables
    client_id = os.environ["ClientID"]
    client_secret = os.environ["ClientSecret"]

    # Get oAuth Token
    token = get_token(client_id, client_secret)

    count_url = "https://intersight.com/api/v1/equipment/Transceivers?$filter=Status ne 'removed'&$count=True"
    response = get_api_data(token, client_id, client_secret, count_url)

    totalcount = response["Count"]
    skip = 0
    count = 0
    json_data = []
    
    while count <= totalcount:
        # Intersight API Path to get Transceiver Details
        data_url = f"https://intersight.com/api/v1/equipment/Transceivers?$select=SwitchId,SlotId,PortId,Name,Vendor,Type,Model,Serial,Status,InterfaceType,Parent,RegisteredDevice,Dn,OperSpeed,OperState,Presence&$expand=RegisteredDevice($select=DeviceHostname,Pid,PlatformType)&$filter=Status ne 'removed'&$top=1000&$skip={skip}"        
        response = get_api_data(token, client_id, client_secret, data_url)
        json_data.extend(response['Results'])
        skip += 1000
        count += 1000

    list_data = []
    fields = ['fi_name', 'fi_Pid', 'fi_serial', 'port_name', 'transceiver_Type', 'transceiver_Model', 'transceiver_Serial', 'transceiver_Vendor', 'transceiver_InterfaceType', 'transceiver_OperSpeed', 'transceiver_Presence', 'transceiver_OperState', 'transceiver_Dn']
    list_data.append(','.join(fields))
    for i in json_data:
        port_list = []
        fi_DeviceHostname = i["RegisteredDevice"]['DeviceHostname'][0]
        port_list.append(f"{fi_DeviceHostname}_FI{i["SwitchId"]}")
        port_list.append(i["RegisteredDevice"]["Pid"][0])
        port_list.append((i["Dn"].split('/')[0]).split('-')[1])
        port_list.append(f"Port {i["SlotId"]}/{i["PortId"]}")
        port_list.append(i["Type"])
        port_list.append(i["Model"])
        port_list.append(i["Serial"])
        port_list.append(i["Vendor"])
        port_list.append(i["InterfaceType"])
        port_list.append(i["OperSpeed"])
        port_list.append(i["Presence"])
        port_list.append(i["OperState"])
        port_list.append(i["Dn"])

        list_data.append(','.join(port_list))

    with open('data.csv', 'w') as f:
       for row in list_data:
           f.write(row + "\n")    
