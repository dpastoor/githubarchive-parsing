import sys
import wget
import calendar
import ujson
import gzip
import matplotlib
import pandas
import os
import re
import time
import pprint
import importlib
import psycopg2

db_con = None
db_con = psycopg2.connect(database='halcyon', user='postgres', password='hi')
# cursor = db_con.cursor()

# Parsing Functions

def parse_pull_request_events(json_data):
    result = {'event': 'PullRequestEvent'}
    result['repo_id'] = json_data['payload']['pull_request']['base']['repo']['id']
    result['repo_name'] = json_data['payload']['pull_request']['base']['repo']['name']
    result['description'] = json_data['payload']['pull_request']['base']['repo']['description']
    result['language'] = json_data['payload']['pull_request']['base']['repo']['language']
    result['stargazers_count'] = json_data['payload']['pull_request']['base']['repo']['stargazers_count']
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
    result["stargazers_count"] = json_data['payload']['pull_request']['base']['repo']["stargazers_count"]
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
    result['stargazers_count'] = json['payload']['forkee']['stargazers_count']
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

def parse_date(date):
  # takes in a date of the form YYYY-MM-DD-HH, for ex: 2016-02-01-15
  url = 'http://data.githubarchive.org/'+ date +'.json.gz'
  filename = wget.download(url)
  # parse out events
  fork_event = []
  watch_event = []
  pr_event = []
  pr_reviewcomment_event = []
  with gzip.open( date+'.json.gz') as f:
      for i, line in enumerate(f):
          json_data = ujson.loads(line)
          if (json_data["type"] == "ForkEvent"):
              fork_event.append(parse_fork_event(json_data))
          elif (json_data["type"] == "WatchEvent"):
              watch_event.append(parse_watch_event(json_data))
          elif (json_data["type"] == "PullRequestEvent"):
              pr_event.append(parse_pull_request_events(json_data))
          elif (json_data["type"] == "PullRequestReviewCommentEvent"):
              pr_reviewcomment_event.append(parse_pull_request_review_comment_events(json_data))
      f.close()
  # Convert to pandas dataframes
  watch_df = pandas.DataFrame.from_dict(watch_event, orient='columns', dtype=None)
  fork_df = pandas.DataFrame.from_dict(fork_event, orient='columns', dtype=None)
  pr_df = pandas.DataFrame.from_dict(pr_event, orient='columns', dtype=None)
  pr_rc_df = pandas.DataFrame.from_dict(pr_reviewcomment_event, orient='columns', dtype=None)
  combined = pandas.concat([pr_df, pr_rc_df, fork_df])
  # munge/reformat and insert repository information into DB
  latest_by_repoid = combined.sort('created_at', ascending= False).drop_duplicates(subset="repo_id")
  latest_by_repoid['description'] = latest_by_repoid['description'].fillna('') # get rid of nans
  latest_by_repoid['org_id'] = latest_by_repoid['org_id'].fillna(0) # org_id of 0 means no org associated
  repo_info = latest_by_repoid[['repo_id', 'repo_name', 'description', 'language', 'stargazers_count', 'org_id']]
  # upsert repo information into postgres
  cursor = db_con.cursor()
  for index, row in repo_info.iterrows():
      sql_str = """INSERT INTO halcyon."Test_Repos" ( id, name, description, language, num_stars, org) \
                   VALUES (%s, %s, %s, %s, %s, %s) \
                   ON CONFLICT (id) DO UPDATE SET \
                   name=excluded.name, description=excluded.description, \
                   language=excluded.language, num_stars=excluded.num_stars;"""   
      cursor.execute(sql_str, (row['repo_id'], row['repo_name'], row['description'], row['language'], row['stargazers_count'], row['org_id']))
  db_con.commit()
  # do the same for watch events
  watch_df['date'] = watch_df['created_at'].map(lambda date_str: date_str.split('T')[0])
  watch_df['hour'] = watch_df['created_at'].map(lambda date_str: date_str.split('T')[1].split(':')[0])
  grouped_watches = pandas.core.frame.DataFrame({'count' : watch_df.groupby(['repo_id', 'repo_name', 'date', 'hour']).size().order(ascending=False)}).reset_index()
  # insert watch events
  cursor = db_con.cursor()
  for index, row in grouped_watches.iterrows():
      sql_str = """INSERT INTO halcyon."Test_Hourly_Watches" ( repo_id, repo_name, star_count, date, hour) \
                   VALUES (%s, %s, %s, %s, %s);"""
      try:
        cursor.execute(sql_str, (row['repo_id'], row['repo_name'], row['count'], row['date'], row['hour']))
      except:
        print("I can't execute a watch insert!")
  try:
    db_con.commit()
  except:
    print("I can't commit all the watch inserts!")





# Script takes in a date and parses the github archive for that date
# for example, script needs url= 'http://data.githubarchive.org/2016-02-01-15.json.gz'
if __name__ == "__main__":
    try:
        arg1 = sys.argv[1]
    except IndexError:
        print("Usage: myprogram.py <date>\n date: YYYY-MM-DD-HH, for ex: 2016-02-01-15")
        sys.exit(1)

    # start the parser
    parse_date(arg1)
