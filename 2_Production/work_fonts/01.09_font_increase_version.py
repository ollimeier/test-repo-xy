#!/usr/bin/env python3
"""
Post production script to fix: Version

by Olli Meier.
"""

import os
import shutil
from copy import copy, deepcopy
from fontTools.ttLib import TTFont

font_suffixes = {'ttf', 'otf'}

FOLDERS = ['OTF', 'TTF_DESKTOP', 'TTF_WEB', 'VAR_DESKTOP', 'VAR_WEB']
DIR = os.path.dirname(__file__)


def update_version(font_obj, version=None, fontfile_based_on=False, nameID_1234=False):
    # TODO:
    # if None, increase by 0.01.
    # create new name table 1234, with original version.
    # update head.fontRevision as well.

    version_current = deepcopy(font_obj["head"].fontRevision)
    if isinstance(version, float):
        version_new = version
    else:
        version_new = version_current + 0.01

    version_new = float("{:.2f}".format(version_new))

    # update name table
    name_table = font_obj['name']
    for rec in name_table.names:
        if rec.nameID in {5, }:
            rec.string = f'Version {version_new}'


    if fontfile_based_on:
        nameID_1234 = f"This font is based on {fontfile_based_on} Version {version_current:.3f}"

    if nameID_1234:
        name_table.setName(nameID_1234, 1234, 3, 1, 0x409) # Win

    font_obj["head"].fontRevision = version_new



def fix_font(dir_path, filename):
    font_path = os.path.join(dir_path, filename)
    font_obj = TTFont(font_path)

    # Becuase the STAT table has been generated after adding the name IDs (in Verison 1.04), there are name entries inbetween. 
    # Therefore we need to get the last name ID which is free for all fonts.
    font_obj['name'].setName("Version 1.05: Increase version (because DW has cache issues with some apps). (2025/08/07 all fonts recreated with new version number)", 1242, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.06: Increase version (because DW has cache issues with some apps). (2025/08/13 all fonts recreated with new version number)", 1243, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.07: Arabic numbers at arabic unicodes and persian numbers at persian unicodes. (2025/08/15 all fonts recreated with new version number)", 1244, 3, 1, 0x409) # Win
    update_version(font_obj, version=1.07)
    if "CFF " in font_obj:
        cff = font_obj['CFF ']
        cff_top_dict = cff.cff.topDictIndex[0]
        cff_top_dict.version = "1.07"

    # update name table unique ID
    name_table = font_obj['name']
    for rec in name_table.names:
        if rec.nameID in {3, }:
            name = name_table.getDebugName(3)
            #rec.string = name.replace("WERK1.06", "1.06;WERK")
            rec.string = ";".join(["1.07"] + name.split(";")[1:])

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



