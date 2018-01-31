# This is a quick hack for cross-cluster migration (only available in the RHV API now).
VERSION='0.0.1'

from curlRHV import curlRHV

XMLT  = "<action>\n"
XMLT += '  <cluster id="TARGETCLUSTERID"/>\n'
XMLT += "</action>"

# cluster1 = 8826f188-af59-44bc-a257-ca1df19fbbd0
# cluster2 = bc28b818-0c82-43c7-b27e-f0bab706ff46
XML   = XMLT.replace("TARGETCLUSTERID", "bc28b818-0c82-43c7-b27e-f0bab706ff46")
vmid  = "02557f24-502b-49ab-afba-73995e148d75"

# Search for VM
cr = curlRHV('/vms/' + vmid + '/migrate', XML)
print(cr)

# EOF
