import sys
from time import *

def printf(text, nline=True):
  '''
  Scroll a given string instead of instant printing
  '''
  for char in text:
    sys.stdout.write(char)
    sys.stdout.flush()
    sleep(0.03)
  if nline:
    sys.stdout.write('\n')

def inputf(text):
  '''
  Scroll an input query
  '''
  printf(text, False)
  return input('')

def log(text):
    '''
    Write a string to the log.txt, Only used for Debugging the Server
    '''
    with open('log.txt') as f:
        t = f.read()
    with open('log.txt', 'w') as f:
        t += '\n{}'.format(text)
        f.write(t)
