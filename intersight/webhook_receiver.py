#!/usr/bin/env python3
"""
    Python Script to Receive Webhook events from Intersigh and send to WebEx teamspace
"""

from flask import Flask, request, Response, abort
from pprint import pprint
import requests

app = Flask(__name__)

def webex_post(createtime,AffectedMoDisplayName,code,description):
    #Post a message to WebEx teamspace using Webex API
    WEBEX_ROOM = "Replace with WebEx RoomId"  # Update
    WEBEX_TOKEN = "Replace with WebEx API Token" # Update
    url = "https://webexapis.com/v1/messages"
    headers = {
            "Authorization": f"Bearer {WEBEX_TOKEN}",
            "Content-Type": "application/json"
    }
    card_payload = {
        "type": "AdaptiveCard",
        "body": [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "items": [
                            {
                                "type": "Image",
                                "style": "Person",
                                "url": "https://developer.webex.com/images/webex-logo-icon-non-contained.svg",
                                "size": "Medium",
                                "height": "50px"
                            }
                        ],
                        "width": "auto"
                    },
                    {
                        "type": "Column",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "Intersight Notification",
                                "weight": "Lighter",
                                "color": "Accent"
                            },
                            {
                                "type": "TextBlock",
                                "weight": "Bolder",
                                "text": "Critical Alarm",
                                "horizontalAlignment": "Left",
                                "wrap": True,
                                "color": "Light",
                                "size": "Large",
                                "spacing": "Small"
                            }
                        ],
                        "width": "stretch"
                    }
                ]
            },
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": 35,
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "Create Time:",
                                "color": "Light"
                            },
                            {
                                "type": "TextBlock",
                                "text": "AffectedMoDisplayName:",
                                "weight": "Lighter",
                                "color": "Light",
                                "spacing": "Small"
                            },
                            {
                                "type": "TextBlock",
                                "text": "Code:",
                                "weight": "Lighter",
                                "color": "Light",
                                "spacing": "Small"
                            }
                        ]
                    },
                    {
                        "type": "Column",
                        "width": 65,
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": createtime,
                                "color": "Light"
                            },
                            {
                                "type": "TextBlock",
                                "text": AffectedMoDisplayName,
                                "color": "Light",
                                "weight": "Lighter",
                                "spacing": "Small"
                            },
                            {
                                "type": "TextBlock",
                                "text": code,
                                "weight": "Lighter",
                                "color": "Light",
                                "spacing": "Small"
                            }
                        ]
                    }
                ],
                "spacing": "Padding",
                "horizontalAlignment": "Center"
            },
            {
                "type": "TextBlock",
                "text": description,
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Resources:"
            },
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "Image",
                                "altText": "",
                                "url": "https://developer.webex.com/images/link-icon.png",
                                "size": "Small",
                                "width": "30px"
                            }
                        ],
                        "spacing": "Small"
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "[Intersight Alarms Reference Guide](https://www.cisco.com/c/en/us/td/docs/unified_computing/Intersight/IMM_Alarms_Guide/b_cisco_intersight_alarms_reference_guide/m_intro_intersight_alarms_guide.html)",
                                "horizontalAlignment": "Left",
                                "size": "Medium"
                            }
                        ],
                        "verticalContentAlignment": "Center",
                        "horizontalAlignment": "Left",
                        "spacing": "Small"
                    }
                ]
            },
            {
                "type": "ActionSet",
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Subscribe to Release Notes",
                        "data": {
                            "subscribe": True
                        }
                    }
                ],
                "horizontalAlignment": "Left",
                "spacing": "None"
            }
        ],
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.3"
        }
    message_payload = {
        "roomId": WEBEX_ROOM,
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_payload
            }
        ],
        "text": f"New Critical Alarm: {code}"
    }

    response = requests.post(url, json=message_payload, headers=headers)
    return response


@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        print("Webhook Received")
        # pprint(request.json)
        print("-" * 60)
        data = request.json
        # pprint(data)
        if data["Event"] != None:
            AffectedMoDisplayName = data["Event"]["AffectedMoDisplayName"]
            Code                  = data["Event"]["Code"]
            CreateTime            = data["Event"]["CreateTime"]
            Description           = data["Event"]["Description"]
            response = webex_post(CreateTime,AffectedMoDisplayName,Code,Description)
            print(response.status_code)
            return Response(status=200)
        else:
            return "Empty Event Data"
    else:
        abort(400)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
