# autosnap.py
#
#    Automate snapshots in RHV
#
VERSION='0.0.1'

import pycurl
import yaml
import datetime
import os
from curlRHV import curlRHV
from xml.etree import ElementTree
from io import BytesIO
from time import sleep
from sys import argv
from sys import exit

# Load configuration variables
autosnapfp = os.path.dirname(os.path.realpath(__file__))
config     = yaml.load(file(autosnapfp + '/autosnap.yml'))
dryrun     = config['dryrun']
splen      = len(config['snap_prefix'])

# Function to verify all snapshots are in the 'ok' state.
def checkSnapStateOK(vmid):
  snapStateOk = True
  qsnaps = curlRHV('/vms/' + vmid + '/snapshots')
  replytree = ElementTree.fromstring(qsnaps)
  vm_snaps = replytree.find(".")
  #print('Snapshots:')
  for vm_snap in vm_snaps.iter('snapshot'):
    #ElementTree.dump(vm_snap);
    vm_snap_id   = vm_snap.attrib['id']
    vm_snap_desc = vm_snap.find('description')
    vm_snap_stat = vm_snap.find('snapshot_status')
    #print('  - "' + vm_snap_desc.text + '" = ' + vm_snap_id + ' (' + vm_snap_stat.text + ')');
    if vm_snap_stat.text != 'ok':
      snapStateOk = False
  return snapStateOk

def listSnapsToDelete(vmid, keepN = 4):
  snaps = []
  qsnaps = curlRHV('/vms/' + vmid + '/snapshots')
  replytree = ElementTree.fromstring(qsnaps)
  vm_snaps = replytree.find(".")
  #print('Snapshots:')
  for vm_snap in vm_snaps.iter('snapshot'):
    #ElementTree.dump(vm_snap);
    vm_snap_id   = vm_snap.attrib['id']
    vm_snap_desc = vm_snap.find('description')
    vm_snap_stat = vm_snap.find('snapshot_status')
    #print('  - "' + vm_snap_desc.text + '" = ' + vm_snap_id + ' (' + vm_snap_stat.text + ')');
    if len(vm_snap_desc.text) >= splen:
      if config['snap_prefix'] in vm_snap_desc.text[:splen]:
        # Found an autosnap snapshot
        snaps.append(vm_snap_desc.text + '=' + vm_snap_id)
  # We only want to keep the last N (keepN).
  snaps = sorted(snaps)
  if len(snaps) > keepN:
    snaps = sorted(snaps)
    snaps = snaps[:-keepN]
  else:
    snaps = []
  return snaps

# Arguments?
if len(argv) > 1:
  # Help?
  if argv[1] in ['-?', '-h', '-help', '--help']:
    print('Syntax: This command takes no arguments.')
    exit(0)
  # Version?
  if argv[1] in ['-V', '-v', '-version', '--version']:
    print('Client version: ' + VERSION)
    exit(0)
  # Use --live or --dryrun to override autosnap.yml
  if argv[1] in ['--live']:
    dryrun = False
  if argv[1] in ['--dryrun']:
    dryrun = True

# XML template for snapshot creation
xmlreqt  = '<snapshot>'
xmlreqt +=   '<description>' + config['snap_prefix'] + '_THISDTS</description>'
xmlreqt +=   '<persist_memorystate>false</persist_memorystate>'
xmlreqt += '</snapshot>'

# Add snapshots to the VMs listed in the config file.
for vm in config['backups']:
  # Now to query snapshots.
  print('VM=' + vm['name'] + ', VMID=' + vm['vmid'])
  snapStateOk = checkSnapStateOK( vm['vmid'] )
  if not snapStateOk:
    print('!!! Snapshot status not OK. Forcing DRYRUN mode...')
    dryrun = True

  # Replace the placeholders with the proper values
  dtstamp  = datetime.datetime.now().__format__(config['snap_date_format'])
  xmlreq   = xmlreqt.replace('THISDTS', dtstamp)
  #print(xmlreq);

  # Use Curl to send the request.
  if not dryrun:
    csnap = curlRHV('/vms/' + vm['vmid'] + '/snapshots/', xmlreq)
    replytree = ElementTree.fromstring(csnap)
    replyroot = replytree.find(".")
    print('New snapshot: name=' + replyroot.find('description').text + ', status=' + replyroot.find('creation_status').text)
  else:
    print('Dryrun! No snapshot taken (hypothetical snapshot name: ' + config['snap_prefix'] + '_' + dtstamp + ').')

  # Wait for snapshot to complete.
  if not dryrun:
    done_waiting = False
    while not done_waiting:
      sleep(config['refresh_timer'])
      snapStateOk = checkSnapStateOK( vm['vmid'] )
      if snapStateOk:
        done_waiting = True

  # Delete snapshots over limit.
  if not dryrun:
    snapDelList = listSnapsToDelete(vm['vmid'], vm['keep'])
    #print(snapDelList)
    for snap in snapDelList:
      snapname,snapid = snap.split("=")
      print("Deleting snapshot: name=[" + snapname + "], snapshot id=[" + snapid + "]")
      dsnap = curlRHV('/vms/' + vm['vmid'] + '/snapshots/' + snapid + '/?async=false', None, 'DELETE')
      #print(dsnap)

      # Wait for the snapshot to delete...
      done_waiting = False
      while not done_waiting:
        sleep(config['refresh_timer'])
        snapStateOk = checkSnapStateOK( vm['vmid'] )
        if snapStateOk:
          done_waiting = True

# EOF
