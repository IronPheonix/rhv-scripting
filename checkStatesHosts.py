# 
VERSION='0.0.1'

import pycurl
import yaml
import datetime
from curlRHV import curlRHV
from xml.etree import ElementTree
from io import BytesIO
from time import sleep
from sys import argv
from sys import exit

# Set some variables
report_all = False
other_detail = False
hosts_up = 0
hosts_down = 0
hosts_maintenance = 0
hosts_maintenance_list = ''
hosts_other = 0
hosts_other_list = ''

# NRPE Return Codes
NRPE_OK = 0
NRPE_OK_TEXT = "OK"
NRPE_WARN = 1
NRPE_WARN_TEXT = "WARNING"
NRPE_CRIT = 2
NRPE_CRIT_TEXT = "CRITICAL"
NRPE_UNKN = 3
NRPE_UNKN_TEXT = "UNKNOWN"

# Default to OK
nrpe_rc = NRPE_OK
nrpe_rc_text = NRPE_OK_TEXT

# Arguments?
if len(argv) > 1:
  # Help?
  if argv[1] in ['-?', '-h', '-help', '--help']:
    print('Syntax: secrets.')
    exit(0)
  # Version?
  if argv[1] in ['-V', '-v', '-version', '--version']:
    print('Client version: ' + VERSION)
    exit(0)

# Get data on all VMs
cr = curlRHV('/hosts')
#print(cr)

# Parse ReplyXML to ElementTree
replyXML = ElementTree.fromstring(cr).find(".")

# Header when printing all VM states.
if report_all:
  print('Host States:')

# Loop over the VMs
for host in replyXML.iter('host'):
  #ElementTree.dump(vm);
  host_name  = host.find('name')
  host_id    = host.attrib['id']
  host_state = host.find('status')
  if report_all:
    print('  - "' + host_name.text + '" = ' + host_id + ', state = ' + host_state.text);
  else:
    if host_state.text in ['up']:
      hosts_up += 1
    elif host_state.text in ['down']:
      hosts_down += 1
      if nrpe_rc < NRPE_WARN:
        nrpe_rc = NRPE_WARN
        nrpe_rc_text = NRPE_WARN_TEXT
    elif host_state.text in ['maintenance','installing']:
      hosts_maintenance += 1
      hosts_maintenance_list += host_name.text + ','
    else:
      hosts_other += 1
      hosts_other_list += host_name.text + ','
      nrpe_rc = NRPE_CRIT
      nrpe_rc_text = NRPE_CRIT_TEXT

# Report Summary.
summary  = 'up=' + str(hosts_up) + ', down=' + str(hosts_down)
summary +=', maintenance=' + str(hosts_maintenance) + ', other=' + str(hosts_other)
output  = 'RHV Hosts(s) ' + nrpe_rc_text + ' : ' + summary
if other_detail and hosts_other > 0:
  output += ' (' + hosts_other_list + ')'
output += ' | ' + summary
print(output)
exit(nrpe_rc)

# EOF
