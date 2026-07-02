#!/usr/bin/env python3
"""

Post production script
by Olli Meier.

"""


import os
import shutil
import time
from copy import copy, deepcopy
from fontTools.ttLib import TTFont
from fontTools import subset

from gftools.fix import (
    fix_fs_selection, 
    fix_mac_style, 
    add_dummy_dsig,
    fix_hinted_font)


font_suffixes = {'ttf', 'otf'}
FOLDERS = ['OTF', 'TTF_DESKTOP', 'VAR_DESKTOP']
DIR = os.path.dirname(__file__)


def find_and_replace_name_table(font_obj, find, replace, ignore_ids={}):
    name_table = font_obj['name']
    for rec in name_table.names:
        if rec.nameID in ignore_ids:
            continue
        if rec.nameID in {3, 6, }:
            s = f'{rec}'.replace(find.replace(' ', ''), replace.replace(' ', ''))
        else:
            s = f'{rec}'.replace(find, replace)
        rec.string = s


def make_tabular_figures_default(dir_path, filename):
    font_obj = TTFont(os.path.join(dir_path, filename))

    uni_mapping = {
    'zero': 0x0030,
    'one': 0x0031,
    'two': 0x0032,
    'three': 0x0033,
    'four': 0x0034,
    'five': 0x0035,
    'six': 0x0036,
    'seven': 0x0037,
    'eight': 0x0038,
    'nine': 0x0039,
    }
    new_glyph_mapping = {}
    for glyph_id, glyph_name in enumerate(font_obj.getGlyphOrder()):
        if glyph_name.endswith('.tf'):
            basename = glyph_name[:-3]
            
            uni_code = uni_mapping.get(basename)
            if uni_code:
                new_glyph_mapping[uni_code] = glyph_name

    for subtable in font_obj['cmap'].tables:
        for k, v in subtable.cmap.items():
            if k in new_glyph_mapping:
                subtable.cmap[k] = new_glyph_mapping[k]

    family_name = font_obj['name'].getBestFamilyName()
    find_and_replace_name_table(font_obj, family_name, f'{family_name} TF')
    output_path = os.path.join(dir_path, filename.replace(family_name.replace(' ', ''), f'{family_name} TF'.replace(' ', '')))
    
    font_obj.save(output_path)
    font_obj.close()


def rename_font(dir_path, filename, name_extention_before='', name_extention_after=''):
    if not name_extention_before and not name_extention_after:
        return
    input_path = os.path.join(dir_path, filename)
    font_obj = TTFont(os.path.join(dir_path, filename))

    family_name = font_obj['name'].getBestFamilyName()
    before_name = f'{name_extention_before} ' if name_extention_before else ''
    after_name = f' {name_extention_after}' if name_extention_after else ''
    subset_name = '{}{}{}'.format(before_name, family_name, after_name)
    find_and_replace_name_table(font_obj, family_name, subset_name, ignore_ids={7, 9})

    file_name = filename.replace(family_name.replace(' ', ''), subset_name.replace(' ', ''))

    output_path = os.path.join(dir_path, file_name)
    print('output_path: ', output_path)
    font_obj.save(output_path)
    #font_obj.close()
    return font_obj, output_path


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
    #font_obj = TTFont(font_path)

    '''
    update_version(font_obj, version=1.01)
    name_table = font_obj['name']
    for rec in name_table.names:
        if rec.nameID in {10, }: #description
            old_str = rec.toUnicode()
            new_str = old_str + f"\nVersion 1.01: Added a kern table for legacy apps + created extra set of fonts (extension 'TF') with tabular figures as default."
            rec.string = new_str
    '''
    #print('font_path: ', font_path)
    #font_obj.save(font_path)

    path_head_tail = os.path.split(font_path)
    make_tabular_figures_default(path_head_tail[0], path_head_tail[1])



def run_post_script(path):
    for filename in os.listdir(path):
        print('filename: ', filename)
        if "Farsi" in filename:
            continue
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



