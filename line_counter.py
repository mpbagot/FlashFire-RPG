import os

total = 0
comments = 0
files = []
for filename in os.listdir():
    if filename.endswith('.py') and filename != 'line_counter.py':
        for line in open(filename).read().split('\n'):
            total += 1 if line != '' and not line.strip().startswith('#') else 0
            comments += 1 if line.strip().startswith('#') else 0
        files.append(filename)

print("Files Scanned: \n - {}".format('\n - '.join(files)))
print("Lines of Code: {}\nComments: {}".format(total, comments))
print("Code to Comment Ratio: {} : 1".format(round(total/comments, 2)))
