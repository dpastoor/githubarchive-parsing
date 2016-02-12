import subprocess

# get all of december
DATE='2016-01-'
for day in range(1, 32):
  if day < 10:
    date_day = DATE + '0' + str(day) + '-'
  else:
    date_day = DATE + str(day) + '-'

  for hour in range(0,24):
    date = date_day+str(hour)
    print(date)
    subprocess.call(['python', 'parse_gha_without_wget.py', '/Volumes/WD2TB/raw_github/'+date])
