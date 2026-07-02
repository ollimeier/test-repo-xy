#!/usr/bin/env python3
"""

Post production script
by Olli Meier.

"""


import os
from copy import copy, deepcopy

from fontTools.ttLib import TTFont, newTable
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
import pathops

from ttfautohint import ttfautohint

from gftools.fix import fix_unhinted_font


font_suffixes = {'ttf', 'otf'}
FOLDERS = ['VAR_DESKTOP', 'VAR_WEB']
DIR = os.path.dirname(__file__)


def create_gasp(font_obj):
    gasp_tbl = newTable("gasp")
    gasp_tbl.gaspRange = {65535: 10} # V1: default: doGray + symmetricSmoothing 
    #gasp_tbl.gaspRange = {65535: 15} # V2: default: gridFit + symmetricGridFit
    #gasp_tbl.gaspRange = {8: 10, 65535: 15} # V3: google way, based on https://googlefonts.github.io/how-to-hint-variable-fonts/
    gasp_tbl.version = 1
    font_obj['gasp'] = gasp_tbl


def update_version(font_obj, version=None, fontfile_based_on=False):
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
        name_table.setName(f"This font is based on {fontfile_based_on} Version {version_current:.3f}", 1234, 3, 1, 0x409) # Win

    font_obj["head"].fontRevision = version_new




def fix_font(dir_path, filename):
    font_path = os.path.join(dir_path, filename)
    font_obj = TTFont(font_path)

    if 'gvar' in font_obj:
        #create_gasp(font_obj)
        fix_unhinted_font(font_obj)


    #update_version(font_obj, version=1.01)
    #font_obj['name'].setName(f"Version 1.01: New web font subsets, based on DW requirements.", 1236, 3, 1, 0x409) # Win
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
        if any([True for x in ['_TRIALS', 'WEB', '_archive', '.idea', 'fonts_exported_from_Glyphs'] if x in os.path.normpath(root).split(os.path.sep)]):
            # skip fonts in these folders.
            # will be created later.
            continue

        path, folder = os.path.split(root)
        if folder in FOLDERS:
            run_post_script(root)


if __name__ == "__main__":
    main()



