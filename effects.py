import sys
from time import *
import pygame
import math

pygame.init()

sfx = pygame.mixer.Channel(0)
main = pygame.mixer.Channel(1)

def play_intro(filename):
    for line in open('cutscene/'+filename).read().split('\n'):
        if line:
            # If the line has a play_music command
            if line.split()[0] == 'play_music':
                # Just play the sound file is asks for
                play_music(line.split()[1])
                continue
            # IF the line has a play command
            elif line.split()[0] == 'play':
                # Play the Sound FX it asks for
                play_sound(line.split()[1])
                continue
            # IF the line is a - or /
            if line in ('-','/'):
                # Print a blank line
                print()
                if line == '/':
                    # Pause for a second
                    sleep(1)
                continue
            # Print the line
            printf(str(line),pause = 0.03)
    # Pause and clear the screen
    sleep(5)
    print('\n'*30)

def printf(text, nline=True,pause=0.015):
  '''
  Scroll a given string instead of instant printing
  '''
  for char in text:
    # Iterate the characters
    # And write them
    sys.stdout.write(char)
    sys.stdout.flush()
    # Pause for a few milliseconds
    sleep(pause)
  if nline:
    # Print a new line
    sys.stdout.write('\n')

def inputf(text):
  '''
  Scroll an input query
  '''
  printf(text, False)
  return input('')

def stop_sound():
    '''
    Stop all currently playing sounds
    '''
    global main
    global sfx
    main.unpause()
    pygame.mixer.music.fadeout(1000)
    sfx.stop()

def play_main():
    '''
    Start the main background music
    '''
    global main
    pygame.mixer.music.fadeout(1000)
    s = pygame.mixer.Sound('sound/music/main_back.ogg')
    main.play(s, loops=-1)

def play_sound(sname):
    '''
    Play the sound on the SFX channel with the given name
    '''
    global sfx
    sfx.stop()
    sound = pygame.mixer.Sound('sound/fx/{}.ogg'.format(sname))
    sfx.play(sound)

def play_music(mname):
    '''
    Play background music with the given name
    '''
    global main
    main.pause()
    pygame.mixer.music.fadeout(1000)
    pygame.mixer.music.load('sound/music/{}.ogg'.format(mname))
    pygame.mixer.music.play(loops=-1)

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
