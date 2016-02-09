#import parse_gha.py
import subprocess


DATE='2016-02-07-'

for hour in range(0,24):
  date = DATE+str(hour)
  print(date)
  subprocess.run(['python', 'parse_gha.py', date])