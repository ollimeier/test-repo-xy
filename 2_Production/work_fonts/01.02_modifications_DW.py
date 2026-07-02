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
from fontTools.varLib import instancer

from gftools.fix import (
    add_dummy_dsig,)

font_suffixes = {'ttf', 'otf'}
FOLDERS = ['OTF', 'TTF_DESKTOP', 'TTF_WEB', 'VAR_WEB', 'VAR_DESKTOP']
DIR = os.path.dirname(__file__)

optical_size_names = ['Text', 'Micro', 'Display', 'Headline', 'Poster']
other_name_extentions = ['VAR', ]

# NOTE: 2025/04/23 As discussed with Ivo (with Version 1.04), we undo the following change of swapping the arabic and persian numbers.

# def map_persian_figures_to_arabic_and_persian_unicodes(font_obj):

#     new_glyph_mapping = {
#     0x06F0: 'zero-persian',
#     0x06F1: 'one-persian',
#     0x06F2: 'two-persian',
#     0x06F3: 'three-persian',
#     0x06F4: 'four-persian',
#     0x06F5: 'five-persian',
#     0x06F6: 'six-persian',
#     0x06F7: 'seven-persian',
#     0x06F8: 'eight-persian',
#     0x06F9: 'nine-persian',

#     # the following unicode mapping is wrong,
#     # but requested by the customer DW (2024/02/08)
#     0x0660: 'zero-persian',
#     0x0661: 'one-persian',
#     0x0662: 'two-persian',
#     0x0663: 'three-persian',
#     0x0664: 'four-persian',
#     0x0665: 'five-persian',
#     0x0666: 'six-persian',
#     0x0667: 'seven-persian',
#     0x0668: 'eight-persian',
#     0x0669: 'nine-persian',

#     }

#     # swapping figures
#     for subtable in font_obj['cmap'].tables:
#         for k, v in subtable.cmap.items():
#             if k in new_glyph_mapping:
#                 subtable.cmap[k] = new_glyph_mapping[k]

#     return font_obj


# def make_persian_figures_default(font_obj):

#     # original mapping:
#     uni_mapping_persian = {
#     'zero-persian': 0x06F0,
#     'one-persian': 0x06F1,
#     'two-persian': 0x06F2,
#     'three-persian': 0x06F3,
#     'four-persian': 0x06F4,
#     'five-persian': 0x06F5,
#     'six-persian': 0x06F6,
#     'seven-persian': 0x06F7,
#     'eight-persian': 0x06F8,
#     'nine-persian': 0x06F9,
#     }

#     uni_mapping_arabic = {
#     'zero-ar': 0x0660,
#     'one-ar': 0x0661,
#     'two-ar': 0x0662,
#     'three-ar': 0x0663,
#     'four-ar': 0x0664,
#     'five-ar': 0x0665,
#     'six-ar': 0x0666,
#     'seven-ar': 0x0667,
#     'eight-ar': 0x0668,
#     'nine-ar': 0x0669,
#     }

#     # prepare: swap figures
#     new_glyph_mapping = {}
#     for glyph_name_persian in uni_mapping_persian:
#         basename = glyph_name_persian.split('-')[0]
#         glyph_name_ar = f"{basename}-ar"
        
#         uni_ar = uni_mapping_arabic[glyph_name_ar]
#         uni_persion = uni_mapping_persian[glyph_name_persian]

#         new_glyph_mapping[uni_persion] = glyph_name_ar
#         new_glyph_mapping[uni_ar] = glyph_name_persian

#     # swapping figures
#     for subtable in font_obj['cmap'].tables:
#         for k, v in subtable.cmap.items():
#             if k in new_glyph_mapping:
#                 subtable.cmap[k] = new_glyph_mapping[k]


#     #font_obj['name'].setName('Swapped arabic and persian figures – this is a custom request (2023/05/25).', 1235, 3, 1, 0x409) # Win

#     return font_obj


def fix_cff_names(font_obj):
    if 'CFF ' not in font_obj:
        return
    
    cff_table = font_obj['CFF ']
    name_table = font_obj['name']

    cff_table.cff.fontNames[0] = name_table.getDebugName(6)
    cff_table.cff.topDictIndex[0].FullName = name_table.getBestFullName()
    cff_table.cff.topDictIndex[0].FamilyName = name_table.getBestFamilyName()
    cff_table.cff.topDictIndex[0].Weight = name_table.getBestSubFamilyName()


def get_instance_postscript_nameIDs(font_obj):
    ps_name_ids = set()

    if 'fvar' not in font_obj:
        return ps_name_ids

    for instance in font_obj['fvar'].instances:
        if isinstance(instance.postscriptNameID, int):
            ps_name_ids.add(instance.postscriptNameID)

    return ps_name_ids


def find_and_replace_name_table(font_obj, find, replace, ignore_ids={}):
    name_table = font_obj['name']
    
    ps_nameIDs = set([3, 6, 25]) # default IDs
    ps_nameIDs.update(get_instance_postscript_nameIDs(font_obj))

    for rec in name_table.names:
        if rec.nameID in ignore_ids:
            continue
        if rec.nameID in ps_nameIDs:
            s = f'{rec}'.replace(find.replace(' ', ''), replace.replace(' ', ''))
        else:
            s = f'{rec}'.replace(find, replace)

        rec.string = s


def shorten_name(font_obj, file_name, name, short_name):
    if name.lower() not in file_name.lower():
        return file_name
    find_and_replace_name_table(font_obj, name, short_name, ignore_ids={7, 9})
    return file_name.replace(name, short_name)


def rename_font(dir_path, filename, name_extention_before=None, name_extention_after=None, skip=()):
    if name_extention_before is None and name_extention_after is None:
        return None, None

    input_path = os.path.join(dir_path, filename)
    font_obj = TTFont(os.path.join(dir_path, filename))

    if 'gvar' in font_obj and 'variable' in skip:
        # skip all variable fonts.
        return None, None

    if 'gvar' not in font_obj and 'static' in skip:
        # skip all static fonts.
        return None, None

    family_name = font_obj['name'].getBestFamilyName()
    family_name_base = family_name
    name_extention = ''
    for name_ext in optical_size_names + other_name_extentions:
        if name_ext in family_name.split(' '):
            name_extention += f' {name_ext}'
            family_name_base = family_name_base.replace(name_extention, '')

    before_name = f'{name_extention_before} ' if name_extention_before else ''
    after_name = f' {name_extention_after}' if name_extention_after else ''
    subset_name = '{}{}{}{}'.format(before_name, family_name_base, after_name, name_extention)
    print('(before_name, family_name, after_name, name_extention): ', (before_name, family_name, after_name, name_extention))
    find_and_replace_name_table(font_obj, family_name, subset_name, ignore_ids={7, 9})

    file_name = filename.replace(family_name.replace(' ', ''), subset_name.replace(' ', ''))
    #file_name = shorten_name(font_obj, file_name, 'Arabic', 'AR')
    #file_name = shorten_name(font_obj, file_name, 'SemiBold', 'SemiBd') This is not required, because it's a microsoft bug. Please see: https://feedbackportal.microsoft.com/feedback/idea/40b6a603-617d-ed11-a81b-000d3ae32cd0

    output_path = os.path.join(dir_path, file_name)
    print('output_path: ', output_path)
    font_obj.save(output_path)
    #font_obj.close()
    return font_obj, output_path


def subset_fonts(font_obj, glyphs_encoded=[0x0041, 0x004C, 0x004C, 0x0049], glyphs_unencoded=['.notdef', '.null', 'null', 'NULL']):

    opts = subset.Options()
    opts.name_IDs = ["*"]
    opts.name_legacy = True
    opts.name_languages = ["*"]
    opts.layout_features = ["*"]
    opts.recalc_timestamp = True
    opts.canonical_order = True
    opts.ignore_missing_glyphs = True
    opts.glyph_names = True
    opts.notdef_outline = True
    # opts.obfuscate_names = True # this would be interesting for creating webfonts.
    # opts.flavor = None  # May be 'woff' or 'woff2'
    
    # for more options please see:
    # https://github.com/fonttools/fonttools/blob/31ba5e6b2428b088df6d0db029ac4e7d3d49bcd4/Lib/fontTools/subset/__init__.py#L2612

    subsetter = subset.Subsetter(options=opts)
    #font_obj = subset.load_font(input_path, opts)


    subsetter.populate(glyphs=glyphs_unencoded, unicodes=glyphs_encoded)
    subsetter.subset(font_obj)

    #subset.save_font(font_obj, input_path, opts)
    #font_obj.close()

    return font_obj
    # Keep in mind a different solution:
    # subset.main([fontpath, "--unicodes=U+0041,U+0028,U+0302,U+1D400,U+1D435", "--output-file=%s" % subsetpath])


def remove_mac_names(font_obj):
    name_table_obj = font_obj['name']
    name_table_obj.removeNames(platformID=1)
    print('Removed all mac name table entries.')


def create_mac_names(font_obj):
    # create mac names based on windows names.
    name_table = font_obj['name']
    win_names = {}
    for rec in name_table.names:
        win_names[rec.nameID] = f'{rec}'

    for name_id, name_str in win_names.items():
        name_table.setName(name_str, name_id, 1, 0, 0)
        print('Created mac name table entry: ', name_id, name_str)




def change_font_embedding(font_obj, level='Print and Preview'):
    #0x0000: "Installable Embedding" -> 0b0000 (binary code)
    #0x0002: "Restricted License Embedding" -> 0b0010 (binary code)
    #0x0004: "Preview & Print Embedding" -> 0b0100 (binary code)
    #0x0008: "Editable Embedding" -> 0b1000 (binary code)

    if level.lower() == 'installable embedding':
        font_obj["OS/2"].fsType = 0x0000
    elif level.lower() == 'restricted license embedding':
        font_obj["OS/2"].fsType = 0x0002
    elif level.lower() == 'editable embedding':
        font_obj["OS/2"].fsType = 0x0008
    else:
        # default is Print and Preview
        font_obj["OS/2"].fsType = 0x0004


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




def fix_font(font_obj, font_path):

    #font_obj = make_persian_figures_default(font_obj)
    # font_obj = map_persian_figures_to_arabic_and_persian_unicodes(font_obj)
    change_font_embedding(font_obj, level='editable embedding')
    remove_mac_names(font_obj)
    # Christoph wünscht explizit Mac names für Custom Projekte.
    # Darum werden die in der nächsten Zeile erstellt, basierend auf den Windows names.
    if 'gvar' not in font_obj:
        # Christoph: Mac Names können in VAR auf jeden Fall erstmal raus, da es sie auch bisher nicht gab
        create_mac_names(font_obj)
    fix_cff_names(font_obj)
    add_dummy_dsig(font_obj)

    return font_obj


def run_post_script(path):
    for filename in os.listdir(path):
        print('filename: ', filename)
        full_path = os.path.join(path, filename)
        print("PATH: {}".format(full_path))
        suffix = filename.split('.')[-1]

        if suffix.lower() in font_suffixes:
            print("\tIt's a font file.")
            
            font_obj, font_path = rename_font(path, filename, name_extention_before='DW')

            fix_font(font_obj, font_path)
            
            font_obj.save(font_path)

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



