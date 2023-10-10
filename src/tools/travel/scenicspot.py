import urllib.request
import ssl
import json
from urllib.parse import urlencode

host = 'https://scenicspot.market.alicloudapi.com'
path = '/lianzhuo/scenicspot'
method = 'GET'
appcode = 'ed529179ac804e72b475fc69a8f12a81'

# Parameters include 'province', 'city', 'spot', 'page'
def get_api_recommendation(city, page=1):
    new_query_parameters = {
        'city': city,
        'page': page,
    }
    # Query
    encoded_query_parameters = urlencode(new_query_parameters)
    url = host + path + '?' + encoded_query_parameters
    request = urllib.request.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    response = urllib.request.urlopen(request, context=ctx)
    content = response.read()
    if content:
        content_str = content.decode('utf-8')
        # Parse the JSON data
        data = json.loads(content_str)
        # Better output formatting
        pretty_json = eval(json.dumps(data, indent=4, ensure_ascii=False))
        return pretty_json
