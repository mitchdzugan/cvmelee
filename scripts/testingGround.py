import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from CVMelee.MeleeYoutubeProcessor import MeleeYoutubeProcessor

MeleeYoutubeProcessor("1FQENHDa3rQ").run()