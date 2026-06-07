from moviepy import *
import moviepy
import os
import re

def fade(file):
    clip = VideoFileClip(file)
    clip = moviepy.video.fx.FadeIn(1.0).apply(clip)
    clip = moviepy.video.fx.FadeOut(1.0).apply(clip)
    return clip

clips = []

i = 1
moreClipsToProcess = True
while(moreClipsToProcess):
    file = str(i) + ".mp4"
    print("Checking: " + file)
    if os.path.exists(file) != True:
        moreClipsToProcess = False
        break
    clip = fade(file)
    clips.append(clip)
    i = i + 1

final = concatenate_videoclips(clips)

path = os.getcwd().split("\\")
outputFile = path[-2] + " - " + path[-1] + ".mp4"

final.write_videofile(outputFile)