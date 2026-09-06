"""把本地的 CLICS event feed 还原成 DOMjudge REST API 的返回值。

`/scoreboard` 不在 event feed 里，因此按 ICPC 规则（罚时 + 首次通过时间）自行计算。
"""
import collections
import json
from pathlib import Path

def parse_event_feed(path):
    singles, lists = {}, collections.defaultdict(dict)
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line == "":
            continue
        event = json.loads(line)
        type, data = event['type'], event.get('data')
        if type in ['contest', 'state']:
            singles[type] = data
            continue
        id = event.get('id') or (data or {}).get('id')
        if data == None:            # 删除事件
            lists[type].pop(id, None)
        else:
            lists[type][id] = data
    return singles, lists

def build_scoreboard(contest, lists, judgements):
    judgement_types = { judgement_type['id']: judgement_type for judgement_type in lists['judgement-types'].values() }
    group_ids = [group['id'] for group in lists['groups'].values() if not group.get('hidden')]
    same = lambda x, y: list(set(x) & set(y))
    func = lambda team: len(same(team.get('group_ids') or [], group_ids))
    teams = list(filter(func, lists['teams'].values()))
    verdict = { judgement['submission_id']: judgement_types[judgement['judgement_type_id']] for judgement in judgements }
    penalty = contest.get('penalty_time', 20)
    minutes = lambda contest_time: reduce_minutes(contest_time)

    submissions = collections.defaultdict(lambda: collections.defaultdict(list))
    for submission in sorted(lists['submissions'].values(), key=lambda submission: int(submission['id'])):
        submissions[submission['team_id']][submission['problem_id']].append(submission)

    rows = []
    for team in teams:
        num_solved, total_time = 0, 0
        for problem_submissions in submissions.get(team['id'], {}).values():
            tries = 0
            for submission in problem_submissions:
                judgement_type = verdict.get(submission['id'])
                if judgement_type == None:
                    continue
                if judgement_type['solved']:
                    num_solved += 1
                    total_time += minutes(submission['contest_time']) + penalty * tries
                    break
                if judgement_type.get('penalty', True):
                    tries += 1
        rows.append({ 'team_id': team['id'], 'score': { 'num_solved': num_solved, 'total_time': total_time } })
    rows.sort(key = lambda row: (-row['score']['num_solved'], row['score']['total_time']))
    return { 'rows': rows }

def reduce_minutes(contest_time):
    hour, minute, _ = contest_time.split(':')
    return int(hour) * 60 + int(minute)

def event_feed_to_api(path):
    """返回 {API method: 返回值}，与 DOMjudge 的 REST API 一一对应"""
    singles, lists = parse_event_feed(path)
    # 未评测完的 judgement 没有 judgement_type_id，跳过
    judgements = [judgement for judgement in lists['judgements'].values() if judgement.get('judgement_type_id')]
    api = {
        '/': singles['contest'],
        '/state': singles['state'],
        '/judgements': judgements,
        '/scoreboard': build_scoreboard(singles['contest'], lists, judgements),
    }
    for type in ['groups', 'languages', 'organizations', 'teams', 'problems', 'judgement-types', 'submissions', 'runs']:
        api['/' + type] = list(lists[type].values())
    return api
