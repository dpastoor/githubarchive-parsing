def parse_pull_request_events(json_data):
    result = {'event': 'PullRequestEvent'}
    result['repo_id'] = json_data['payload']['pull_request']['base']['repo']['id'] 
    result['repo_name'] = json_data['payload']['pull_request']['base']['repo']['name']
    result['description'] = json_data['payload']['pull_request']['base']['repo']['description']
    result['language'] = json_data['payload']['pull_request']['base']['repo']['language']
    result['created_at'] = json_data['created_at']
    result['actor_id'] = json_data['actor']['id']
    result['actor_login'] = json_data['actor']['login']
    result['org'] = False
    result['org_id'] = None
    if 'org' in json_data:
        result['org'] = True
        result['org_id'] = json_data['org']['id']
    return result

def parse_pull_request_review_comment_events(json_data):
    result = {'event': 'PullRequestReviewCommentEvent'}
    result['language'] = json_data['payload']['pull_request']['base']['repo']['language'] 
    result['repo_id'] = json_data['payload']['pull_request']['base']['repo']['id'] 
    result['repo_name'] = json_data['payload']['pull_request']['base']['repo']['full_name'] 
    result['created_at'] = json_data['created_at']
    result['actor_id'] = json_data['actor']['id']
    result['actor_login'] = json_data['actor']['login']
    result['org'] = False
    result['org_id'] = None
    if 'org' in json_data:
        result['org'] = True
        result['org_id'] = json_data['org']['id']
    return result

def parse_fork_event(json):
    result = {}
    result['event'] = 'ForkEvent'
    result['repo_id'] = json['repo']['id']
    result['repo_name'] = json['repo']['name']
    result['actor_id'] = json['actor']['id']
    result['actor_login'] = json['actor']['login']
    result['org'] = False
    result['org_id'] = None
    result['created_at'] = json['created_at']
    result['language'] = json['payload']['forkee']['language']
    if 'org' in json:
        result['org'] = json['org']['id']
        result['org_id'] = json['org']['id']     
    return result

def parse_watch_event(json_data):
    result = {}
    result['created_at'] = json_data["created_at"]
    result['event'] = "WatchEvent"
    result['repo_id'] = json_data["repo"]["id"]
    result['repo_name'] = json_data["repo"]["name"]
    result['action'] = json_data["payload"]["action"]
    result['actor_id'] = json_data["actor"]["id"]
    result['actor_login'] = json_data["actor"]["login"]
    result['org'] = False
    result['org_id'] =  None
    if 'org' in json_data:
        result['org'] = True
        result['org_id'] = json_data["org"]["id"]
    return result