
# coding: utf-8

# In[1]:
import calendar
import ujson
import gzip
import pandas
import os
## functions
import github_parsing_functions as ghp
import logging
## --- create parsing times ---
## this will create an array of arrays, with each subarray consisting of all hours in that day as file name
## <year>-<month>-<day>-<hour>.json.gz
parse_dates_array = []
parse_dates = []
YEAR = 2016
MON = 1
days = calendar.monthrange(YEAR,MON)[1]
month = str(MON) if MON > 9 else "0" + str(MON)
logging.basicConfig(filename= "parse_data_{0}_{1}.log".format(YEAR, month), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level = logging.INFO)
for day in range(1, days+1):
    single_day = []
    day_str = str(day) if day > 9 else "0" + str(day)
    for hour in range(0, 24):
        single_day.append(str(YEAR) + "-" + month + "-" + day_str + "-" + str(hour) + ".json.gz")
    parse_dates_array.append(single_day)
    parse_dates.append(str(YEAR) + "-" + month + "-" + day_str)

def process_day(date_index, day_array):
    fork_event = []
    watch_event = []
    pr_event = []
    pr_reviewcomment_event = []

    for hour_file in day_array:
        if os.path.isfile("../raw_data/" + hour_file):
            logging.info('starting on file: ' + hour_file)
            with gzip.open("../raw_data/" + hour_file) as f:
                for i, line in enumerate(f):
                    json_data = ujson.loads(line)
                    if (json_data["type"] == "ForkEvent"):
                        fork_event.append(ghp.parse_fork_event(json_data))
                    elif (json_data["type"] == "WatchEvent"):
                        watch_event.append(ghp.parse_watch_event(json_data))
                    elif (json_data["type"] == "PullRequestEvent"):
                        pr_event.append(ghp.parse_pull_request_events(json_data))
                    elif (json_data["type"] == "PullRequestReviewCommentEvent"):
                        pr_reviewcomment_event.append(ghp.parse_pull_request_review_comment_events(json_data))
                f.close()
        else:
            logging.warning('WARNING: could not find file: ' + hour_file)

    watch_df = pandas.DataFrame.from_dict(watch_event, orient='columns', dtype=None)
    fork_df = pandas.DataFrame.from_dict(fork_event, orient='columns', dtype=None)
    pr_df = pandas.DataFrame.from_dict(pr_event, orient='columns', dtype=None)
    pr_rc_df = pandas.DataFrame.from_dict(pr_reviewcomment_event, orient='columns', dtype=None)



    frames = [pr_df, pr_rc_df, fork_df]
    combined = pandas.concat(frames)

    latest_by_repoid = combined.sort_values('created_at', ascending= False).drop_duplicates(subset="repo_id")
    latest_by_repoid['description'] = latest_by_repoid['description'].fillna('') # get rid of nans
    latest_by_repoid['org_id'] = latest_by_repoid['org_id'].fillna(0) # org_id of 0 means no org associated

    repo_info = latest_by_repoid[['repo_id', 'repo_name', 'description', 'language', 'stargazers_count', 'org_id']]


    watch_df['date'] = watch_df['created_at'].map(lambda date_str: date_str.split('T')[0])
    watch_df['hour'] = watch_df['created_at'].map(lambda date_str: date_str.split('T')[1].split(':')[0])



    watch_df.to_csv("parsed_data/" + parse_dates[date_index] + '_watch_df.csv.gz', compression="gzip")
    repo_info.to_csv("parsed_data/" + parse_dates[date_index] + '_repo_info.csv.gz', compression="gzip")

for i, day_array in enumerate(parse_dates_array):
    print("starting on day: " + str(i))
    process_day(i, day_array)
