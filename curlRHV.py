# Module for calling RHV's REST API via cURL
VERSION='0.0.1'

import pycurl
import yaml
import os
from io import BytesIO

# HTTP request to RHV via cURL
def curlRHV(apiPath, xmlText = None, httpOp = None):
  # Default to POST, check for GET,
  # other HTTP operations handled by httpOp
  httpPost = 1;
  if xmlText is None:
    httpPost = 0;

  # We need a buffer to store the HTTP response.
  httpBuffer = BytesIO()

  # Load configuration settings
  curlrhvloc = os.path.dirname(os.path.realpath(__file__))
  config     = yaml.load(file(curlrhvloc + '/settings.yml'))

  # Create cURL request.
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://' + config['server_address'] + config['server_api_path'] + apiPath)
  c.setopt(c.HTTPHEADER, ['User-Agent: curlRHV/' + VERSION, 'Content-Type: application/xml'])
  c.setopt(c.USERPWD, config['auth_username'] + ':' + config['auth_password'])

  # Is this a POST, GET, something else?
  if httpOp is None:
    c.setopt(c.POST, httpPost)
  else:
    c.setopt(c.CUSTOMREQUEST, httpOp)

  # Send the xmlText if defined.
  if xmlText is not None:
    c.setopt(c.POSTFIELDS, xmlText)

  # Send the request
  c.setopt(c.WRITEFUNCTION, httpBuffer.write)
  c.perform()
  c.close()

  # Return HTTP response
  return httpBuffer.getvalue().decode('iso-8859-1')

# EOF
