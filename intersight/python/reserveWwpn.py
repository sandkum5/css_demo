#!/usr/bin/env python3
"""
    - Reserve WWPNs and assign to a profile vHBAs
    - Uses Intersight OAuth 2.0 Authentication
    - Ensure WWPN's are not in use.

    Pre-requisites:
    - Organization
    - WWPN Pool
    - Server Profiles with no SAN Connectivity Policy
    - SAN Connectivity Policy

    Sample Output:
    ❯ ./demo_v2.py
    Server Profile: demo1 WWPNs associated successfully!
      vhba0: 20:00:00:25:B5:AA:AA:31
      vhba1: 20:00:00:25:B5:AA:AA:32
    Server Profile: demo2 WWPNs associated successfully!
      vhba0: 20:00:00:25:B5:AA:AA:21
      vhba1: 20:00:00:25:B5:AA:AA:22
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

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
        return response.json()['Results'][0]

def post_api_data(token, client_id, client_secret, api_url, post_data):
    """ Get API Endpoint Data """
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url=api_url, headers=headers, data=post_data)
    if	response.status_code == 401:
        print("Existing Token Expired. Generating a new one!")
        token = get_token(client_id, client_secret)
        post_api_data(token, client_id, client_secret, api_url, post_data)
    else:
        return response.json()

def create_wwpn_reservations(org_moid, fcpool_moid, wwpn):
    """
        Create WWPN Reservations
    """
    res_url = f"https://intersight.com/api/v1/fcpool/Reservations"
    wwpn_res_moids = {}
    for key,value in wwpn.items():
        vhba_data = {
            "AllocationType": "dynamic",
            "IdPurpose": "WWPN",
            "Identity": f"{value}",
            "Organization": {
                "ClassId": "mo.MoRef",
                "Moid": f"{org_moid}",
                "ObjectType": "organization.Organization",
                "link": f"https://intersight.com/api/v1/organization/Organizations/{org_moid}"
            },
            "Pool": {
                "ClassId": "mo.MoRef",
                "Moid": f"{fcpool_moid}",
                "ObjectType": "fcpool.Pool",
                "link": f"https://intersight.com/api/v1/fcpool/Pools/{fcpool_moid}"    
            }
        }

        vhba_json = json.dumps(vhba_data)
        vhba_res_data = post_api_data(token, client_id, client_secret, res_url, vhba_json)
        wwpn_res_moids[key] = vhba_res_data['Moid']
    return wwpn_res_moids

def add_res_ref_to_profile(sp_moid, wwpn_res_moids):
    """
        Add Reservation References to the Profile
    """
    rr_url = f"https://intersight.com/api/v1/server/Profiles/{sp_moid}"
    rr_vhba_data = {"ReservationReferences": []}
    for vhba_name,wwpn_res_moid in wwpn_res_moids.items(): 
        res_data = {
            "ClassId": "fcpool.ReservationReference",
            "ConsumerName": f"{vhba_name}",
            "ConsumerType": "Vhba",
            "ObjectType": "fcpool.ReservationReference",
            "ReservationMoid": f"{wwpn_res_moid}"
        }
        rr_vhba_data["ReservationReferences"].append(res_data)

    rr_vhba_json = json.dumps(rr_vhba_data)
    vhba_rr_data = post_api_data(token, client_id, client_secret, rr_url, rr_vhba_json)
    return vhba_rr_data

def add_sanconn_policy_to_profile(sp_moid, sanpolicy_moid, sp_data):
    """
        Associate SAN Connectivity Policy to the Profile
    """
    sp_post_url = f"https://intersight.com/api/v1/server/Profiles/{sp_moid}"
    san_policy_data = {
        "ClassId": "mo.MoRef",
        "Moid": f"{sanpolicy_moid}",
        "ObjectType": "vnic.SanConnectivityPolicy",
        "link": f"https://intersight.com/api/v1/vnic/SanConnectivityPolicies/{sanpolicy_moid}"
    }

    post_data = { "PolicyBucket": sp_data['PolicyBucket']}  
    post_data['PolicyBucket'].append(san_policy_data)
    policy_bucket_json = json.dumps(post_data)

    updated_sp_data = post_api_data(token, client_id, client_secret, sp_post_url, policy_bucket_json)
    return updated_sp_data


if __name__ == '__main__':
    # Variables
    client_id     = os.getenv("ClientId")
    client_secret = os.getenv("ClientSecret")

    with open('py_input.json') as f:
        data = json.load(f)

    for server in data:
        org_name            = server['org_name']
        fcpool_name         = server['fcpool_name']
        sp_name             = server['sp_name']
        sanconn_policy_name = server['sanconn_policy_name']
        vhba0_name          = server['vhba0_name']
        vhba1_name          = server['vhba1_name']
        wwpn = {
            "vhba0": server['vhba0_wwpn'],
            "vhba1": server['vhba1_wwpn']
        }

        # URLs    
        org_url             = f"https://intersight.com/api/v1/organization/Organizations?$filter=Name eq '{org_name}'"
        fcpool_url          = f"https://intersight.com/api/v1/fcpool/Pools?$filter=Name eq '{fcpool_name}'"
        sp_url              = f"https://intersight.com/api/v1/server/Profiles?$filter=Name eq '{sp_name}'"
        san_conn_url        = f"https://intersight.com/api/v1/vnic/SanConnectivityPolicies?$filter=Name eq '{sanconn_policy_name}'"

        # Get oAuth Token
        token = get_token(client_id, client_secret)

        # Get API Endpoint Data
        # Get Org, WWPN Pool and Server Profile Info
        org_data       = get_api_data(token, client_id, client_secret, org_url)
        sp_data        = get_api_data(token, client_id, client_secret, sp_url)
        fcpool_data    = get_api_data(token, client_id, client_secret, fcpool_url)
        sanpolicy_data = get_api_data(token, client_id, client_secret, san_conn_url)

        # Get Moids
        org_moid = org_data['Moid']
        sp_moid = sp_data['Moid']
        fcpool_moid = fcpool_data['Moid']
        sanpolicy_moid = sanpolicy_data['Moid']

        # Create WWPN Reservations
        wwpn_res_moids = create_wwpn_reservations(org_moid, fcpool_moid, wwpn)

        # Add Reservation References to the Profile
        vhba_rr_data = add_res_ref_to_profile(sp_moid, wwpn_res_moids)

        # Associate SAN Connectivity Policy to the Profile
        updated_sp_data = add_sanconn_policy_to_profile(sp_moid, sanpolicy_moid, sp_data)

        print(f"Server Profile: {sp_name} WWPNs associated successfully!")
        for key,value in wwpn.items():
            print(f"  {key}: {value}")
