#!/usr/bin/env python3
"""
    Script to get UCS Blade Servers in IMM and UCSM Domain with No Profiles

    Uses Intersight oAuth Authentication. 
    Create oAuth App under Intersight > Settings > oAuth 2.0 > Create oAuth 2.0  to get the ClientID and ClientSecret.

    Python libraries needed to run this script:
      pip install python-dotenv requests
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

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
    # print("Successfuly obtained a new token")
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
    get_profiles_url = "https://intersight.com/api/v1/server/Profiles?$top=1000&$select=Name,AssignedServer,ConfigChangeContext,ConfigContext,DeployStatus,ServerAssignmentMode,ServerPool,TargetPlatform"

    # Get oAuth Token
    token = get_token(client_id, client_secret)

    # Get Server Profile Data
    server_profiles = get_api_data(token, client_id, client_secret, get_profiles_url)

    # Get Server Moids with Profiles
    server_moid_with_profiles = []
    for profile in server_profiles['Results']:
        if profile['AssignedServer'] != None:
            server_moid_with_profiles.append(profile['AssignedServer']['Moid'])

    # Get Blade Server Data
    get_blades_url = "https://intersight.com/api/v1/compute/Blades?$top=1000"
    imm_blades = get_api_data(token, client_id, client_secret, get_blades_url)

    # Get Blade Moids
    imm_blade_moids = []
    for blade in imm_blades['Results']:
        imm_blade_moids.append(blade['Moid'])

    # Get Server Moids without Profiles
    server_moids_without_profile = []
    for blade_moid in imm_blade_moids:
        if blade_moid not in server_moid_with_profiles:
            server_moids_without_profile.append(blade_moid)

    print("")
    print("Servers with No Profiles:")

    # Print IMM Blade Servers with No Profiles
    print("  IMM Blade Servers:")
    for moid in server_moids_without_profile:
        for server in imm_blades['Results']:
            if server['Moid'] == moid and server['ManagementMode'] == "Intersight":
                print(f"    Chassis_{server['ChassisId']}/Slot_{server['SlotId']}, Serial: {server['Serial']}, Name: {server['Name']}")
                # print(f"    Moid: {server['Moid']}, Serial: {server['Serial']}, Name: {server['Name']}")


    # Print UCSM Blade Servers with No Profiles
    print("")
    print("  UCSM Blade Servers:")
    for server in imm_blades['Results']:
        if server['ManagementMode'] == "UCSM" and server['ServiceProfile'] == '':
            print(f"    Chassis_{server['ChassisId']}/Slot_{server['SlotId']}, Serial: {server['Serial']}, Name: {server['Name']}")
            # print(f"    Moid: {server['Moid']}, Serial: {server['Serial']}, Name: {server['Name']}")
