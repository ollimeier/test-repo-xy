#!/usr/bin/env python3
"""
Post production script to fix:

by Olli Meier.
"""


import os
import shutil
from subprocess import call
import subprocess
from fontTools.ttLib import TTFont
from fontTools.varLib.featureVars import sortFeatureList

font_suffixes = {'ttf', 'otf'}

FOLDERS = ['OTF', 'TTF_DESKTOP', 'TTF_WEB', 'VAR_DESKTOP', 'VAR_WEB']
DIR = os.path.dirname(__file__)


def fix_ots_warning_feature_order(font_obj):
    # ots-sanitize passed this file, however warnings were printed:
    # WARNING: Layout: tags aren't arranged alphabetically. [code: ots-sanitize-warn]
    # make use of sortFeatureList
    # https://github.com/fonttools/fonttools/blob/54e70b3ceff4d7ed34491a6512fb875408308405/Lib/fontTools/varLib/featureVars.py#L561
    
    sortFeatureList(font_obj['GSUB'].table)
    print("Fixing OTS WARNING: Layout: tags aren't arranged alphabetically.")


def fix_ots_errors(font_obj):
    fix_ots_warning_feature_order(font_obj)



def fix_font(dir_path, filename):
    font_path = os.path.join(dir_path, filename)
    font_obj = TTFont(font_path)

    fix_ots_errors(font_obj)

    print('font_path: ', font_path)
    font_obj.save(font_path)


def run_post_script(path):
    for filename in os.listdir(path):
        print('filename: ', filename)
        full_path = os.path.join(path, filename)
        print("PATH: {}".format(full_path))
        suffix = filename.split('.')[-1]

        if suffix.lower() in font_suffixes:
            #shutil.copyfile(os.path.join(path, filename), os.path.join(DIR_orig, filename))

            print("\tIt's a font file.")
            fix_font(path, filename)
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



