import sys
from time import *
import pygame

pygame.init()

sfx = pygame.mixer.Channel(0)

def printf(text, nline=True):
  '''
  Scroll a given string instead of instant printing
  '''
  for char in text:
    sys.stdout.write(char)
    sys.stdout.flush()
    sleep(0.015)
  if nline:
    sys.stdout.write('\n')

def inputf(text):
  '''
  Scroll an input query
  '''
  printf(text, False)
  return input('')

def play_sound(sname):
    '''
    Play the sound on the SFX channel with the given name
    '''
    pass

def play_music(mname):
    '''
    Play background music with the given name
    '''
    pass

def log(text):
    '''
    Write a string to the log.txt, Only used for Debugging the Server
    '''
    with open('log.txt') as f:
        t = f.read()
    with open('log.txt', 'w') as f:
        t += '\n{}'.format(text)
        f.write(t)
