#!/usr/bin/env python3
"""

Post production script
by Olli Meier.

"""


import os
import shutil
import time


font_suffixes = {'ttf', 'otf'}
FOLDERS = ['OTF', 'TTF_DESKTOP', 'TTF_WEB', 'VAR_DESKTOP', 'VAR_WEB']
DIR = os.path.dirname(__file__)



def run_post_script(path):
    for filename in os.listdir(path):
        #print('filename: ', filename)
        full_path = os.path.join(path, filename)
        #print("PATH: {}".format(full_path))
        suffix = filename.split('.')[-1]

        if suffix.lower() in font_suffixes:
            #shutil.copyfile(os.path.join(path, filename), os.path.join(DIR_orig, filename))

            #print("\tIt's a font file.")

            #fix_font(path, filename)
            if filename[:2] != 'DW':
                print('Removing None-DW font file: ', filename)
                os.remove(full_path)
            continue
        else:
            print("\tIt's NOT a font file.")
            continue


def main(args=None):
    for root, dirs, files in os.walk(DIR):
        if any([True for x in ['_TRIALS', 'WEB', '_archive', '.idea'] if x in os.path.normpath(root).split(os.path.sep)]):
            # skip fonts in these folders.
            # will be created later.
            continue

        path, folder = os.path.split(root)
        if folder in FOLDERS:
            run_post_script(root)


if __name__ == "__main__":
    main()



