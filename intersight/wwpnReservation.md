# Assign WWPN to an HBA in a Server Profile

### Step-1: Create WWPN Pool
### Step-2: Create a Reservation Object - seen under Reserved Identifiers in GUI

```/api/v1/fcpool/Reservations```

```
{
    "AllocationType": "dynamic",
    "IdPurpose": "WWPN",
    "Identity": "20:00:00:25:B5:00:0A:02",
    "Organization": {
        "ClassId": "mo.MoRef",
        "Moid": "xxxxx",
        "ObjectType": "organization.Organization",
        "link": "https://intersight.com/api/v1/organization/Organizations/xxxxx"
    },
    "Pool": {
        "ClassId": "mo.MoRef",
        "Moid": "xxxx1",
        "ObjectType": "fcpool.Pool",
        "link": "https://intersight.com/api/v1/fcpool/Pools/xxxx1"    
    }
}
```

### Step-3: Create a Server Profile with "ReservationReferences" or add "ReservationReferences" attribute to an existing Server Profile

To existing Server Profile:

```/api/v1/server/Profiles/{ServerProfile_Moid}```

```
{
    "ReservationReferences": [
        {
          "ClassId": "fcpool.ReservationReference",
          "ConsumerName": "vhba0",
          "ConsumerType": "Vhba",
          "ObjectType": "fcpool.ReservationReference",
          "ReservationMoid": "xxxxx2"
        }
    ]
}
```

- Get "ReservationMoid" from Step-2
- ConsumerName should be the exact vHBA name we would be creating in the Server Profile under SAN Connectivity Policy

### Step-4: Associate SAN Connectivity Policy to the Server Profile. 

#####Note: Step-3 and 4 can be combined. Will test the behavior once I get a chance.
