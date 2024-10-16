#!/usr/bin/env python3
"""
    Reserve WWPNs and assign to a profile vHBAs
    Uses Intersight OAuth 2.0 Authentication
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
    print("Successfuly obtained a new token")
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

if __name__ == '__main__':
    # Variables
    client_id           = os.getenv("ClientId")
    client_secret       = os.getenv("ClientSecret")
    org_name            = "default"
    fcpool_name         = "demoxwwpn"
    sp_name             = "demo1"
    sanconn_policy_name = "demox"
    vhba0_name          = "vhba0"
    vhba1_name          = "vhba1"
    vhba0_wwpn          = "20:00:00:25:B5:AA:AA:21"
    vhba1_wwpn          = "20:00:00:25:B5:AA:AA:22"

    # URLs    
    org_url             = f"https://intersight.com/api/v1/organization/Organizations?$filter=Name eq '{org_name}'"
    fcpool_url          = f"https://intersight.com/api/v1/fcpool/Pools?$filter=Name eq '{fcpool_name}'"
    sp_url              = f"https://intersight.com/api/v1/server/Profiles?$filter=Name eq '{sp_name}'"
    san_conn_url        = f"https://intersight.com/api/v1/vnic/SanConnectivityPolicies?$filter=Name eq '{sanconn_policy_name}'"

    # Get oAuth Token
    token = get_token(client_id, client_secret)

    # Get API Endpoint Data
    # Get Org, WWPN Pool and Server Profile Info
    org_data = get_api_data(token, client_id, client_secret, org_url)
    fcpool_data = get_api_data(token, client_id, client_secret, fcpool_url)
    sp_data = get_api_data(token, client_id, client_secret, sp_url)
    san_conn_policy_data = get_api_data(token, client_id, client_secret, san_conn_url)

    # Create WWPN Reservations
    res_url = f"https://intersight.com/api/v1/fcpool/Reservations"
    vhba0_data = {
        "AllocationType": "dynamic",
        "IdPurpose": "WWPN",
        "Identity": f"{vhba0_wwpn}",
        "Organization": {
            "ClassId": "mo.MoRef",
            "Moid": f"{org_data['Moid']}",
            "ObjectType": "organization.Organization",
            "link": f"https://intersight.com/api/v1/organization/Organizations/{org_data['Moid']}"
        },
        "Pool": {
            "ClassId": "mo.MoRef",
            "Moid": f"{fcpool_data['Moid']}",
            "ObjectType": "fcpool.Pool",
            "link": f"https://intersight.com/api/v1/fcpool/Pools/{fcpool_data['Moid']}"    
        }
    }
    vhba1_data = {
        "AllocationType": "dynamic",
        "IdPurpose": "WWPN",
        "Identity": f"{vhba1_wwpn}",
        "Organization": {
            "ClassId": "mo.MoRef",
            "Moid": f"{org_data['Moid']}",
            "ObjectType": "organization.Organization",
            "link": f"https://intersight.com/api/v1/organization/Organizations/{org_data['Moid']}"
        },
        "Pool": {
            "ClassId": "mo.MoRef",
            "Moid": f"{fcpool_data['Moid']}",
            "ObjectType": "fcpool.Pool",
            "link": f"https://intersight.com/api/v1/fcpool/Pools/{fcpool_data['Moid']}"    
        }
    }
    vhba0_json = json.dumps(vhba0_data)
    vhba1_json = json.dumps(vhba1_data)
    vhba0_res_data = post_api_data(token, client_id, client_secret, res_url, vhba0_json)
    vhba1_res_data = post_api_data(token, client_id, client_secret, res_url, vhba1_json)
    print("WWPN Reservations Created Successfully!")
    # Add Reservation References to the Profile
    rr_url = f"https://intersight.com/api/v1/server/Profiles/{sp_data['Moid']}"
    rr_vhba_data = {
        "ReservationReferences": [
            {
                "ClassId": "fcpool.ReservationReference",
                "ConsumerName": f"{vhba0_name}",
                "ConsumerType": "Vhba",
                "ObjectType": "fcpool.ReservationReference",
                "ReservationMoid": f"{vhba0_res_data['Moid']}"
            },
            {
                "ClassId": "fcpool.ReservationReference",
                "ConsumerName": f"{vhba1_name}",
                "ConsumerType": "Vhba",
                "ObjectType": "fcpool.ReservationReference",
                "ReservationMoid": f"{vhba1_res_data['Moid']}"
            }
        ]
    }
    rr_vhba_json = json.dumps(rr_vhba_data)
    vhba_rr_data = post_api_data(token, client_id, client_secret, rr_url, rr_vhba_json)
    print("WWPN Reservations Added to the Profile Successfully!")
    # Associate SAN Connectivity Policy to the Profile
    sp_post_url = f"https://intersight.com/api/v1/server/Profiles/{sp_data['Moid']}"
    san_policy_data = {
        "ClassId": "mo.MoRef",
        "Moid": f"{san_conn_policy_data['Moid']}",
        "ObjectType": "vnic.SanConnectivityPolicy",
        "link": f"https://intersight.com/api/v1/vnic/SanConnectivityPolicies/{san_conn_policy_data['Moid']}"
    }

    post_data = { "PolicyBucket": sp_data['PolicyBucket']}  
    post_data['PolicyBucket'].append(san_policy_data)
    policy_bucket_json = json.dumps(post_data)

    updated_sp_data = post_api_data(token, client_id, client_secret, sp_post_url, policy_bucket_json)
    print("SAN Connectivity Policy assigned to the profile Successfully!")
