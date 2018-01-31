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
searchString = ''

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
  # If we get here, assume the argument is a VM ID.
  searchString = argv[1]

# Search for VM
cr = curlRHV('/vms/?search=' + searchString)
#print(cr)

# Parse ReplyXML to ElementTree
replyXML = ElementTree.fromstring(cr).find(".")

# Loop over the matches
print('Matches:')
for vm in replyXML.iter('vm'):
  #ElementTree.dump(vm);
  vm_name = vm.find('name')
  vm_id   = vm.attrib['id']
  print('  - "' + vm_name.text + '" = ' + vm_id);

# EOF
