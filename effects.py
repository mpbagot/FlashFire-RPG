import sys
from time import *
import pygame
import math

pygame.init()

sfx = pygame.mixer.Channel(0)

def play_intro(filename):
    for line in open(filename).read().split('\n'):
        if line:
            if line.split()[0] == 'play_music':
                play_music(line.split()[1])
                continue
            elif line.split()[0] == 'play':
                play_sound(line.split()[1])
                continue
            if line in ('-','/'):
                print()
                if line == '/':
                    sleep(1)
                continue
            printf(str(line),pause = 0.03)
    sleep(5)
    print('\n'*30)

def printf(text, nline=True,pause=0.015):
  '''
  Scroll a given string instead of instant printing
  '''
  for char in text:
    sys.stdout.write(char)
    sys.stdout.flush()
    sleep(pause)
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
    # sound = pygame.mixer.Sound('sound/fx/{}.ogg'.format(sname))
    # sfx.play(sound)
    pass

def play_music(mname):
    '''
    Play background music with the given name
    '''
    # pygame.mixer.music.stop()
    # pygame.mixer.music.load('sound/music/{}.ogg'.format(mname))
    # pygame.mixer.music.play()
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

def get_distance_between(n1, n2):
    '''
    Determine the distance between two nodes (approximately)
    '''
    return int(math.sqrt((n1[0]-n2[0])**2+(n1[1]-n2[1])**2))
