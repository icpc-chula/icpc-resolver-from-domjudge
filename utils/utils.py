from dateutil import parser
from functools import reduce
import datetime
from pathlib import Path
import random
import re
import string

ISO_TIMESTAMP_FRACTION_RE = re.compile(
    r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{4,})(Z|[+-]\d{2}:?\d{2})?$'
)

def api_cache_path(config, method):
    if not config.get('cache_requests', False):
        return None
    endpoint = method.strip('/') or 'contest'
    filename = re.sub(r'[^A-Za-z0-9._-]+', '_', endpoint)
    return Path(config.get('cache_dir', 'api-cache')) / f'{filename}.json'

def dtime2timestamp(dtime):
    return parser.parse(dtime).timestamp()

def ctime2timestamp(ctime):
    return reduce(lambda x, y: 60.0 * float(x) + float(y), ctime.split(':'), 0.0)

def normalize_timestamp(timestamp):
    match = ISO_TIMESTAMP_FRACTION_RE.match(timestamp)
    if match == None:
        return timestamp
    timezone = match.group(3)
    if timezone == None:
        offset = datetime.datetime.now().astimezone().strftime('%z')
        timezone = f'{offset[:3]}:{offset[3:]}'
    return f'{match.group(1)}.{match.group(2)[:3]}{timezone}'

def normalize_event_feed_timestamps(data):
    if type(data) == type(dict()):
        return {
            key: normalize_event_feed_timestamps(value)
            for key, value in data.items()
        }
    if type(data) == type(list()):
        return [normalize_event_feed_timestamps(value) for value in data]
    if type(data) == type(str()):
        return normalize_timestamp(data)
    return data

def randomstr(len):
    return ''.join(random.sample(string.ascii_letters, len))

def make_ordinal(n):
    '''
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    '''
    n = int(n)
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix

def make_ordinal_zh(n):
    n = int(n)
    assert(1 <= n and n <= 3)
    if n == 1:
        return "🏆冠军"
    elif n == 2:
        return "🏆亚军"
    elif n == 3:
        return "🏆季军"
    else:
        assert(1 <= n and n <= 3)
