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
vms_up = 0
vms_down = 0
vms_paused = 0
vms_other = 0
vms_other_list = ''

# How many VMs need to be 'paused' for us to
# start warning?
vms_paused_to_warning = 3

# How many VMs need to be in 'paused' for us
# to switch to critical?
vms_paused_to_critical = 6

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
    exit(3)
  # Version?
  if argv[1] in ['-V', '-v', '-version', '--version']:
    print('Client version: ' + VERSION)
    exit(3)

# Get data on all VMs
cr = curlRHV('/vms')
#print(cr)

# Parse ReplyXML to ElementTree
replyXML = ElementTree.fromstring(cr).find(".")

# Header when printing all VM states.
if report_all:
  print('VM States:')

# Loop over the VMs
for vm in replyXML.iter('vm'):
  #ElementTree.dump(vm);
  vm_name  = vm.find('name')
  vm_id    = vm.attrib['id']
  vm_state = vm.find('status')
  if report_all:
    print('  - "' + vm_name.text + '" = ' + vm_id + ', state = ' + vm_state.text);
  else:
    if vm_state.text in ['up']:
      vms_up += 1
    elif vm_state.text in ['down','suspended']:
      vms_down += 1
    elif vm_state.text in ['paused']:
      vms_paused += 1
      # Need warning?
      if nrpe_rc < NRPE_WARN:
        if vms_paused > vms_paused_to_warning:
          nrpe_rc = NRPE_WARN
          nrpe_rc_text = NRPE_WARN_TEXT
      # Need critical?
      if nrpe_rc < NRPE_CRIT:
        if vms_paused > vms_paused_to_critical:
          nrpe_rc = NRPE_CRIT
          nrpe_rc_text = NRPE_CRIT_TEXT
    else:
      nrpe_rc = NRPE_UNKN
      nrpe_rc_text = NRPE_UNKN_TEXT
      vms_other += 1
      vms_other_list += vm_name.text + ','

# Report Summary.
summary = 'up=' + str(vms_up) + ', down=' + str(vms_down) + ', paused=' + str(vms_paused) + ', other=' + str(vms_other)
output  = 'RHV VM(s) ' + nrpe_rc_text + ' : ' + summary
if other_detail and vms_other > 0:
  output += ' (' + vms_other_list + ')'
output += ' | ' + summary
print(output)
exit(nrpe_rc)

# EOF
