import sys
import xbmc
from urllib.parse import urlparse, parse_qsl
from common import list_objects

handle = int(sys.argv[1])

if __name__ == '__main__':
    # Parse the full plugin URL.
    parsed = urlparse(sys.argv[0])
    # Example result:
    # parsed.path == "/mymethod/"
    # parsed.query == "param1=value1&param2=value2"

    # Strip leading/trailing slashes, split on "/"", take first segment as requested method.
    segments = parsed.path.strip('/').split('/')
    if not segments or not segments[0]:
        xbmc.log('No plugin method supplied', xbmc.LOGERROR)
    method = segments[0]

    # Parse parameters in a dictionary.
    params = {}
    if sys.argv[2] is not None and sys.argv[2] != '':
        params = dict(parse_qsl(sys.argv[2][1:]))
    # Example result: params == {'param1': 'value1', 'param2': 'value2'}

    # Generate list.
    list_objects(method, params, handle)