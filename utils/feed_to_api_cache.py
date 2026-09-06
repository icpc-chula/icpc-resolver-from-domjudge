"""把本地 event feed 转成 api-cache/ 目录，供 cache_requests 使用

    python3 utils/feed_to_api_cache.py <event feed> <api-cache dir>

若只是想直接读本地 event feed，在 config 里设置 "file" 即可，无需本脚本。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.event_feed import event_feed_to_api
from utils.utils import api_cache_path

feed, outdir = sys.argv[1], Path(sys.argv[2])
config = { 'cache_requests': True, 'cache_dir': str(outdir) }
for method, data in event_feed_to_api(feed).items():
    path = api_cache_path(config, method)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    print(f"  {path}  {len(data) if type(data) == type(list()) else 1}")
