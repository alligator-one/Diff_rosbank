from sys import argv
import json,re,os
from io import open
 
# code string to unicode
def unicode_replacement(match):
    char = match.group()
    return r'\\u{:04X}'.format(ord(char))
 
# get variables from diff_git.Jenkinsfile
script, repository, files_names, project_id, merge_id, url_diff, after, namespace, git_user, git_pass, gitlab_token = argv
print('---argv---')
print(argv)
 
# Save text file with changes for Jira sending
def save_txt(fin2):
  string = 'Repository: ' + repository + '\n'
  fin2.write(string)
  string =  'Show in gitlab: ' + url_diff + '/diffs\n'
  fin2.write(string)
  print('---string---\n'+string+'\n')
 
# Save html file with changes for email sending
def save_html(fin):
  string = '<HTML><BODY>'
  fin.write(string)
  string = '<p><b>Repository: ' + repository + '</b></p>'
  fin.write(string)
  string =  '<p>Show in gitlab: ' + '<a>'+ url_diff + '/diffs </a></p>'
  fin.write(string)
 
# get merge request as json
string = 'GITLAB/api/v4/projects/'+ project_id +'/merge_requests/' + merge_id
print('---url: '+string)
 
# Save the comparison result of 2 branches in file diff1.sson
os.system("curl -o diff1.json -k --header 'PRIVATE-TOKEN: " + gitlab_token + "' " + string)
with open('diff1.json') as file:
  diff_dict = json.load(file)
 
# get first & end hash's for comparison
print('---diff_dict---')
print(diff_dict)
print(diff_dict['diff_refs']['base_sha'])
start = diff_dict['diff_refs']['base_sha']
print(diff_dict['diff_refs']['head_sha'])
end = diff_dict['diff_refs']['head_sha']
 
# get task number in Jira
print('---title---')
 
print(diff_dict['title'])
title = diff_dict['title']
 
 
title2 = title
if title[0] == '[':
 
    title2 = title.replace('[' ,'')
 
if title2[len(title2)-1] == ']':
    title2 = title2.replace(']','')
title = title2.replace(" ", "")
 
# get task number in Jira without []
print('---title---')
print(title)
 
# get a difference between 2 branches as a dictionary diff_dict
string = ' "GITLAB/api/v4/projects/' + project_id +'/repository/compare?from='+ start + '&to='+ end +'&straight=true'
string2 = "curl -o diff2.json -kv --header \"PRIVATE-TOKEN: "+ gitlab_token + "\"" +string + "\""
print('--url3:  '+ string2)
os.system(string2)
 
found_file = False
first_file = 0
print(files_names)
 
# show file to degug
with open('diff2.json') as file:
  diff_dict = json.load(file)
print('--diff_dict---')
print(diff_dict)
 
# enumerate in the cycle file names where we are looking for changes
files_names2 = files_names.split(',')
for file_name in files_names2:
  print('----file_name:'+file_name+'----')
 
  # counter for file names in diff_dict
  i = 0
  for i in range(len(diff_dict['diffs'])):
    string = []
   
    # If file name with index i is found in dictionary diff_dict
    # (changes in files has been done, commited and put in merge request)
    if file_name in (diff_dict['diffs'][i]['new_path'][:]):
      print('found file')
      found_file = True
      fin = open("/home/jenkins-agent/workspace/abpm/Experiment/ExamplePipeline/diff/source/diff.html", "ab")
      fin2 = open("/home/jenkins-agent/workspace/abpm/Experiment/ExamplePipeline/diff/source/diff.txt", "ab")
      if first_file == 0:
        save_html(fin)
        save_txt(fin2)
        first_file += 1
 
      # write to file all changes to send comment in jira and emailing
      string = 'env: '+ after+'; repo: '+repository + '; namespace: '+ namespace + '\n'
      fin2.write(string)
 
      string = '<p><b>Changes in file: ' + file_name + '</b></p>'
      print('---string---')
      print(string)
      fin.write(string)
     
      string = 'Changes in file: ' + file_name + '\n'
      fin2.write(string)
      string =  diff_dict['diffs'][i]['diff'].split('\n')
      print(string)
 
      for str_ in string:
 
        # if string contains '-' or '+' copy the string to the file to send because this string
        # is considered as a comment 
        if (str_.startswith('-') or str_.startswith('+')) and len(str_) > 1 :
          string2 = str_ + '</br>'
          string2 = string2.encode('utf-8')
          fin.write(string2)
          string2 = str_ + '\n'
          string2 = string2.encode('utf-8')
          fin2.write(string2)
        i += 1
 
    else:
       #print('---no file diff.html---')
       continue
 
if found_file:
  string = '</HTML></BODY>'
  #print(string)
  fin.write(string)
 
  fin.close()
  fin2.close()
try:
  file = open('/home/jenkins-agent/workspace/abpm/Experiment/ExamplePipeline/diff/source/diff.txt','rt', encoding="utf-8")
except:
  print('---no file diff.txt---')
 
line_2 = ''
for line in file:
    line_ = re.sub(r'.', unicode_replacement, line)
    line_ = line_.replace('\n','\\\\u000a')
    line_2 =  line_2 + line_
line_ = line_2
 
# make decoded to unicode string to put it to Jira
print('---all line---')
print(line_)
file.close()
 
# put comment to Jira
print('---try to send comment to jira 04092024---')
string = 'curl -D- -u '+ git_user +':'+ git_pass +' -X PUT  -H "Content-Type: application/json; charset=UTF-8" -d "{\\\"update\\": {\\\"comment\\": [{\\"add\\": {\\"body\\\": \\\" '+  line_  + \
    '\\"}}]}}" https://JIRA:8443/rest/api/2/issue/' + title + ' --insecure'
 
print(string)
os.system(string)