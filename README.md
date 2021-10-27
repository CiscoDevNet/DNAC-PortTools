# DNAC-PortTools

uses Cisco DNA center API to shut/no shut intefaces on a switch.

## Getting stated
First (optional) step, create a vitualenv. This makes it less likely to clash with other python libraries in future.
Once the virtualenv is created, need to activate it.
```buildoutcfg
python3 -m venv env3
source env3/bin/activate
```

Next clone the code.

```buildoutcfg
git clone https://github.com/CiscoDevNet/DNAC-PortTools.git
```

Then install the  requirements (after upgrading pip). 
Older versions of pip may not install the requirements correctly.
```buildoutcfg
pip install -U pip
pip install -r requirements.txt
```

## Credentials
Edit the dnac_config.py or set shell envionment variables to connect to Cisco DNA center

# Running the tool

Bring up interfacess

```buildoutcfg
./port_tools.py --deviceip 192.168.14.16 --noshut Gig1/0/29,Gig1/0/28
Skipping:Gig1/0/29 op UP
Skipping:Gig1/0/28 op UP
```

shut down
```
./port_tools.py --deviceip 192.168.14.16 --noshut Gig1/0/29,Gig1/0/28 
interface GigabitEthernet1/0/29  no shutdown  exit
interface GigabitEthernet1/0/28  no shutdown  exit
```

same operation again is skipped
```
./port_tools.py --deviceip 192.168.14.16 --shut Gig1/0/29,Gig1/0/28 
Skipping:Gig1/0/29 op DOWN
Skipping:Gig1/0/28 op DOWN

```