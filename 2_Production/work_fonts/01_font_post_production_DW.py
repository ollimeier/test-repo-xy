#!/usr/bin/env python3
"""
Post production script to fix:

by Olli Meier.
"""

#TODO: Fix sorting of fvar instances

import os
import shutil
from copy import copy, deepcopy
from subprocess import call
import subprocess
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.otlLib.builder import buildStatTable #, _addName für später vielleicht hilfreich :)
from fontTools.misc.fixedTools import fixedToFloat

from gftools.fix import (
    fix_fs_selection, 
    fix_mac_style, 
    fix_vertical_metrics,
    add_dummy_dsig,
    fix_hinted_font)

from gftools.utils import mkdir

font_suffixes = {'ttf', 'otf'}

FOLDERS = ['OTF', 'TTF_DESKTOP', 'TTF_WEB', 'VAR_DESKTOP', 'VAR_WEB']
DIR = os.path.dirname(__file__)

# from importlib.machinery import SourceFileLoader

# #fontwerk_spec_folder = os.path.join(DIR.split('Type-Data')[0], 'specifications')
# fontwerk_spec_folder = f"{DIR.split('Fontwerk-Server')[0]}/Fontwerk-Server/Typefaces/specifications/"
# fontwerk_conditions = os.path.join(fontwerk_spec_folder, 'fontwerk_conditions.py')
# conditions = SourceFileLoader("fontwerk.conditions", fontwerk_conditions).load_module()


opsz_values =[
    dict(nominalValue=10, rangeMinValue=fixedToFloat(-0x80000000, 16), rangeMaxValue=14, name="Text"),
    dict(nominalValue=20, rangeMinValue=14, rangeMaxValue=fixedToFloat(0x7FFFFFFF, 16), name="Normal", flags=0x2),
]

wght_values=[
    dict(value=300, name="Light"),
    dict(value=400, linkedValue=700, name="Regular", flags=0x2, ),  # Regular
    dict(value=500, name="Medium"),
    dict(value=600, name="SemiBold"),
    dict(value=700, name="Bold"),

]

# the following way causes issues in Adobe InDesign 2022
'''
wght_values_save=[
    dict(nominalValue=300, rangeMinValue=300, rangeMaxValue=350, name="Light"),
    dict(nominalValue=400, rangeMinValue=350, rangeMaxValue=450, name="Regular", flags=0x2),
    dict(nominalValue=500, rangeMinValue=450, rangeMaxValue=550, name="Medium"),
    dict(nominalValue=600, rangeMinValue=550, rangeMaxValue=650, name="SemiBold"),
    dict(nominalValue=700, rangeMinValue=650, rangeMaxValue=700, name="Bold"),
    dict(value=400, linkedValue=700, name="Regular", flags=0x2, ),  # Regular
]
'''

wdth_values=[
    #dict(nominalValue=50, rangeMinValue=50, rangeMaxValue=56, name="XXCond"),
    dict(nominalValue=62.5, rangeMinValue=56, rangeMaxValue=69, name="XCond"),
    dict(nominalValue=75, rangeMinValue=69, rangeMaxValue=81, name="Cond"),
    dict(nominalValue=87.5, rangeMinValue=81, rangeMaxValue=94, name="SemiCond"),
    dict(nominalValue=100, rangeMinValue=94, rangeMaxValue=100, name="Normal", flags=0x2),
    #dict(nominalValue=112.5, rangeMinValue=106, rangeMaxValue=119, name="SemiWide"),
    #dict(nominalValue=125, rangeMinValue=119, rangeMaxValue=138, name="Wide"),
    #dict(nominalValue=150, rangeMinValue=138, rangeMaxValue=175, name="XWide"),
    #dict(nominalValue=200, rangeMinValue=175, rangeMaxValue=200, name="XXWide"),
]

ital_values_upright=[
    #dict(value=0, name="Upright", flags=0x2, ),
    #dict(value=1, name="Italic", ),
    dict(value=0, linkedValue=1, name="Upright", flags=0x2, ),
    dict(value=1, name="Italic"),
    #dict(nominalValue=0, rangeMinValue=0, rangeMaxValue=1, name="Regular", flags=0x2),
    #dict(value=0, linkedValue=1, name="Regular", flags=0x2, ),  # Regular
]

ital_values_italic=[
    dict(value=1, name="Italic"),
]


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


def get_best_family_name(font_obj):
    for name_id in [21, 16, 1]:
        name = font_obj['name'].getDebugName(name_id)
        if name is not None:
            return name


def create_AXES(font_obj):
    name_table_obj = font_obj['name']
    name_id_2 = name_table_obj.getDebugName(2)

    if name_id_2.lower() == 'italic':
        ital_value = ital_values_italic
    else:
        ital_value = ital_values_upright

    AXES = [
        dict(
            tag="opsz",
            name="Optical size",
            ordering=0,
            values=opsz_values,
        ),
        dict(
            tag="wdth",
            name="Width",
            ordering=1,
            values=wdth_values,
        ),
        dict(
            tag="ital",
            name="Italic",
            ordering=2,
            values=ital_value,
        ),
        dict(
            tag="wght",
            name="Weight",
            ordering=3,
            values=wght_values,
        ),


    ]

    return AXES


def remove_mac_names(font_obj):
    name_table_obj = font_obj['name']
    name_table_obj.removeNames(platformID=1)


def remove_unnecessary_name_ids(font_obj):
    name_table_obj = font_obj['name']
    
    if 'fvar' in font_obj:
        #name ID 16 and 17 are not really needed for variable fonts.
        name_table_obj.removeNames(nameID=16)
        name_table_obj.removeNames(nameID=17)


def fix_instances_postscript_names(font_obj):
    name_table_obj = font_obj['name']

    if 'fvar' not in font_obj:
        # it's not a variable font, 
        # so no fix needed.
        return

    ps_name_ids = dict()
    for instance in font_obj['fvar'].instances:
        # first collect: instance.postscriptNameID
        if isinstance(instance.postscriptNameID, int):
            ps_name_ids[instance.postscriptNameID] = instance.subfamilyNameID

    fam_name = get_best_family_name(font_obj)
    for rec in name_table_obj.names:
        name_id = rec.nameID
        name_str = f'{rec}'

        if name_id < 256:
            # skip all name ids below 255
            continue

        if name_id not in ps_name_ids:
            # skip if it's not a instance PS name
            continue

        new_name_str = f"{fam_name}-{name_table_obj.getDebugName(ps_name_ids[name_id])}".replace(' ', '')
        if new_name_str != name_str:
            rec.string = new_name_str
            print('change from: ', name_str)
            print('change tooo: ', new_name_str)


def fix_bad_version(font_obj):
    head_table = font_obj['head']
    name_table = font_obj['name']

    version_number_head = "{:.2f}".format(head_table.fontRevision)
    version_number_name = name_table.getDebugName(5).split(' ')[-1]

    if version_number_head == version_number_name:
        print('Version looks good.')
        return

    try:
        version_number_head_float = float(version_number_head)
        bad_version_number_head_float = False
    except Exception:
        print('Bad version_number_head: ', version_number_head)
        bad_version_number_head_float = True

    try:
        version_number_name_float = float(version_number_name)
        bad_version_number_name_float = False
    except Exception:
        print('Bad version_number_name: ', version_number_name)
        bad_version_number_name_float = True
    
    if (bad_version_number_name_float and not bad_version_number_head_float) or (version_number_name.strip('0') == version_number_head):
        version_number = version_number_head
        for rec in name_table.names:
            name_str = f'{rec}'
            if version_number_name not in name_str:
                continue

            rec.string = name_str.replace(version_number_name, version_number_head)


def create_STAT(font_obj):
    AXES = create_AXES(font_obj)
    buildStatTable(font_obj, AXES, macNames=False)


def fix_fs_selection_wws(font_obj):
    name_table_obj = font_obj['name']
    name_id_21 = name_table_obj.getDebugName(21)
    name_id_22 = name_table_obj.getDebugName(22)

    if name_id_21 is None and name_id_22 is None:
        fs_selection = font_obj["OS/2"].fsSelection
        fs_selection |= 1 << 8
        font_obj["OS/2"].fsSelection = fs_selection


def fix_weight_class_var(font_obj):
    # this might be obsolete if my PR to gffonts gets accepted.
    if 'fvar' not in font_obj:
        # not a variable font
        return

    fvar = font_obj['fvar']
    default_axis_values = {a.axisTag: a.defaultValue for a in fvar.axes}

    v = default_axis_values.get('wght', None)

    if v is not None:
        if int(v) != font_obj["OS/2"].usWeightClass:
            font_obj["OS/2"].usWeightClass = int(v)
            print('Changed usWeightClass to match fvar default value.')

    # TODO: 
    # Fix name table as well and also look for width class.


def fix_width_class_var(font_obj):
    if 'fvar' not in font_obj:
        # not a variable font
        return

    fvar = font_obj['fvar']
    default_axis_values = {a.axisTag: a.defaultValue for a in fvar.axes}

    k = default_axis_values.get('wdth', None)

    if k is not None:
        v = 5 # default
        for item in conditions._WIDTH_VALUES:
            if k == conditions._WIDTH_VALUES[item]['fvar']:
                v = conditions._WIDTH_VALUES[item]['usWidthClass']
                break
        old_value = font_obj["OS/2"].usWidthClass
        if int(v) != old_value:
            font_obj["OS/2"].usWidthClass = int(v)
            print('Changed usWidthClass from {} to {}'.format(old_value, v))


def remove_var_table_for_static_fonts(font_obj):
    if 'gvar' not in font_obj:
        for table in {'fvar', 'STAT', 'avar'}:
            if table in font_obj:
                del font_obj[table]
                print('Removed table: ', table)


def remove_hinting(font_obj, list_of_glyphs):
    print('list_of_glyphs: ', list_of_glyphs)
    for glyph_name in list_of_glyphs:
        glyph = font_obj['glyf'].get(glyph_name)
        glyph.removeHinting()

def remove_hinting_ttf(font_obj):
    _hinting_tables_default = ["gasp", "cvt ", "cvar", "fpgm", "prep", "hdmx", "VDMX"]

    font_obj["glyf"].removeHinting()

    for table in _hinting_tables_default:
        if table in font_obj:
            del font_obj[table]


def remove_unreachable_glyphs(font_obj):
    # this function removes all unreachable glyphs, 
    # by using fonttools subsetter.

    return subset_fonts(font_obj, glyphs_encoded=font_obj.getBestCmap().keys())


def fix_ots_warning_feature_order(font_obj):
    # ots-sanitize passed this file, however warnings were printed:
    # WARNING: Layout: tags aren't arranged alphabetically. [code: ots-sanitize-warn]
    pass


def fix_ots_errors(font_obj):
    fix_ots_warning_feature_order(font_obj)


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
    
    remove_var_table_for_static_fonts(font_obj)
    font_obj = remove_unreachable_glyphs(font_obj)

    if 'fvar' in font_obj:
        fix_instances_postscript_names(font_obj)
        create_STAT(font_obj)
        fix_weight_class_var(font_obj)
        #fix_width_class_var(font_obj)
        remove_hinting_ttf(font_obj)

    fix_fs_selection(font_obj)
    fix_mac_style(font_obj)
    fix_fs_selection_wws(font_obj)
    fix_hinted_font(font_obj)
    fix_bad_version(font_obj)
    #remove_mac_names(font_obj)
    add_dummy_dsig(font_obj)

    font_obj['name'].setName("Version 1.00: This is a custom font for Deutsche Welle, based on Pangea 2.5. Swapped arabic and persian figures – this is a custom request (2023/05/25)", 1234, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.01: New web font subsets, based on DW requirements. (2023/06/06)", 1235, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.01: Added a kern table for legacy apps + created extra set of fonts (extension 'TF') with tabular figures as default. (2023/12/14 static TTF only)", 1236, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.02: fixed some Arabic ligature issues + Persian numbers as default on Arabic and Persian unicodes. (2024/02/07 all fonts recreated with same version number)", 1237, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.03: fixed Arabic kerning issue alefHamzabelow-ar;@MMK_L_yeh-ar.init;. (2024/05/16 all fonts recreated with new version number)", 1238, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.04: Persian got its own design + separate fonts (therefore undo: Persian numbers as default on Arabic and Persian unicodes). (2025/04/23 all fonts recreated with new version number)", 1239, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.05: Increase version (because DW has cache issues with some apps). (2025/08/07 all fonts recreated with new version number)", 1242, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.06: Increase version (because DW has cache issues with some apps). (2025/08/13 all fonts recreated with new version number)", 1243, 3, 1, 0x409) # Win
    font_obj['name'].setName("Version 1.07: Make sure arabic numbers be arabic and persian numbers be persian. (2025/08/15 all fonts recreated with new version number)", 1244, 3, 1, 0x409) # Win
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



