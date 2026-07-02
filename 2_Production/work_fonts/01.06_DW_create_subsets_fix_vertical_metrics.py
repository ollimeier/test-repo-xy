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
    fix_fs_selection, 
    fix_mac_style, 
    add_dummy_dsig,
    fix_hinted_font,
    fix_unhinted_font)

font_suffixes = {'ttf', 'otf'}
FOLDERS = ['OTF', 'TTF_WEB', 'TTF_DESKTOP', 'VAR_WEB', 'VAR_DESKTOP']
DIR = os.path.dirname(__file__)

optical_size_names = ['Text', 'Micro', 'Display', 'Headline', 'Poster']
other_name_extentions = ['VAR', ]

glyphs_unencoded_basic = ['.notdef', '.null', 'null', 'NULL'] # could include oldstyle figures as well as other unencoded glyphs.

extra_unicodes_latn_ext_compare_to_pangea_var_2000 = set([0x0132, 0x0133, 0x0138, 0x0149, 0x0180, 0x0181, 0x0186, 0x0187, 0x0188, 0x0189, 0x018A, 0x018E, 0x0190, 0x0191, 0x0193, 0x0194, 0x0196, 0x0197, 0x0198, 0x0199, 0x019A, 0x019B, 0x019C, 0x019D, 0x019E, 0x019F, 0x01A4, 0x01A5, 0x01A9, 0x01AA, 0x01AC, 0x01AD, 0x01AE, 0x01B1, 0x01B2, 0x01B3, 0x01B4, 0x01B5, 0x01B6, 0x01B7, 0x01B8, 0x01B9, 0x01C0, 0x01C1, 0x01C2, 0x01C3, 0x01DD, 0x01DE, 0x01DF, 0x01E0, 0x01E1, 0x01E4, 0x01E5, 0x01E8, 0x01E9, 0x01EA, 0x01EB, 0x01EC, 0x01ED, 0x01EE, 0x01EF, 0x01F0, 0x01F4, 0x01F5, 0x01F8, 0x01F9, 0x01FA, 0x01FB, 0x01FC, 0x01FD, 0x01FE, 0x01FF, 0x0200, 0x0201, 0x0202, 0x0203, 0x0204, 0x0205, 0x0206, 0x0207, 0x0208, 0x0209, 0x020A, 0x020B, 0x020C, 0x020D, 0x020E, 0x020F, 0x0210, 0x0211, 0x0212, 0x0213, 0x0214, 0x0215, 0x0216, 0x0217, 0x021C, 0x021D, 0x021E, 0x021F, 0x0220, 0x0226, 0x0227, 0x0228, 0x0229, 0x022A, 0x022B, 0x022C, 0x022D, 0x022E, 0x022F, 0x0230, 0x0231, 0x0238, 0x0239, 0x023A, 0x023B, 0x023C, 0x023D, 0x023E, 0x0241, 0x0242, 0x0243, 0x0244, 0x0245, 0x0246, 0x0247, 0x0248, 0x0249, 0x024A, 0x024B, 0x024C, 0x024D, 0x024E, 0x024F])
list_of_unicodes_for_remove_from_latin_extend_according_DW = set([0x0132, 0x0133, 0x0149, 0x0180, 0x0186, 0x0187, 0x0188, 0x0189, 0x018E, 0x0191, 0x0196, 0x019A, 0x019B, 0x019F, 0x01A4, 0x01A5, 0x01A9, 0x01AA, 0x01AC, 0x01AD, 0x01AE, 0x01B2, 0x01B3, 0x01B4, 0x01B5, 0x01B6, 0x01B7, 0x01B8, 0x01B9, 0x01C0, 0x01C1, 0x01C2, 0x01DD, 0x01DE, 0x01DF, 0x01E0, 0x01E1, 0x01E4, 0x01E5, 0x01EA, 0x01EB, 0x01ED, 0x01EE, 0x01EF, 0x01F0, 0x01F8, 0x01FA, 0x01FB, 0x01FC, 0x01FD, 0x01FE, 0x01FF, 0x0200, 0x0201, 0x0202, 0x0203, 0x0204, 0x0205, 0x0206, 0x0207, 0x0208, 0x0209, 0x020A, 0x020B, 0x020C, 0x020D, 0x0210, 0x0213, 0x021C, 0x021D, 0x021E, 0x021F, 0x0220, 0x0226, 0x0227, 0x022A, 0x022B, 0x022C, 0x022D, 0x022E, 0x022F, 0x0230, 0x0231, 0x0238, 0x0239, 0x023A, 0x023B, 0x023C, 0x023D, 0x023E, 0x0241, 0x0242, 0x0244, 0x0245, 0x0246, 0x0247, 0x0248, 0x0249, 0x024A, 0x024B, 0x024C, 0x024D, 0x024E, 0x024F])

latn_extended_unicodes = set( list([x for x in range(0x00A1, 0x00A9)] + 
                                            [x for x in range(0x00AA, 0x0250)]
                                            )) #['U+00A1-00A8', 'U+00AA-024F']
latn_extended_unicodes -= list_of_unicodes_for_remove_from_latin_extend_according_DW


def make_persian_default_arabic(font_obj):
    print("make_persian_default_arabic: ", font_obj)

    glyph_order = font_obj.getGlyphOrder()
    glyph_order_by_name = {name: i for i, name in enumerate(glyph_order)}
    for glyph_id, glyph_name in enumerate(glyph_order):
        if "-persian" not in glyph_name:
            continue
        glyph_name_ar = glyph_name.replace("-persian", "-ar")
        # glyph_id_ar = glyph_order_by_name.get(glyph_name_ar, None)
        # if glyph_id_ar is None:
        #     continue

        # swapping -ar with -persian
        for subtable in font_obj['cmap'].tables:
            for k, v in subtable.cmap.items():
                if v == glyph_name_ar:
                    subtable.cmap[k] = glyph_name

        print(f"Glyph ID: {glyph_id}, Glyph Name: {glyph_name}")


vmetrics_default = {
    'typo_ascender': 984,
    'typo_descender': -284,
    'typo_linegap': 0,

    'win_ascent': 1134, #1134.0 Abrevehookabove.text Text Bold Italic
    'win_descent': 352, #-352.0 lowlinecomb.text Bold Italic
    
    'hhea_ascent': 984,
    'hhea_descent': -284,
    'hhea_linegap': 0,
}

vmetrics_arabic = {
    'typo_ascender': 984,
    'typo_descender': -284,
    'typo_linegap': 0,

    'win_ascent': 1134,
    'win_descent': 563, # -563.0 e-ar Text Bold Italic
    
    'hhea_ascent': 984,
    'hhea_descent': -284,
    'hhea_linegap': 0,
}

get_subsets = {

    '': {       'glyphs_encoded': '*', 
                'glyphs_unencoded': '*',
                'vmetrics': vmetrics_default,
                'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': (0, 0, 1)}, 
                'variable': True,
                'static': True,
    },

    'Latin Basic Letters': {  
                'glyphs_encoded': set( list([x for x in range(0x0041, 0x005B)] + [x for x in range(0x0061, 0x007B)]) ),  #['U+0041-005A', 'U+0061-007A']
                'glyphs_unencoded': set(glyphs_unencoded_basic),
                'vmetrics': vmetrics_default,
                # 'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': (0, 0, 1)}, 
                #'features': ["rvrn", "ccmp", "liga", "locl", "mark", "mkmk", "rlig"],
                #'features_remove': ["rlig"], 
                'variable': True,
                'static': True,
    },
    
    'Latin Basic Symbols': {  
                'glyphs_encoded': set( list([x for x in range(0x0020, 0x0041)] + 
                                            [x for x in range(0x005B, 0x0061)] +
                                            [x for x in range(0x007B, 0x007F)] +
                                            [0x00A0, 0x00A9]
                                            )),  #['U+0020-0040', 'U+005B-0060', 'U+007B-007E', 'U+00A0', 'U+00A9']
                'glyphs_unencoded': set(glyphs_unencoded_basic),
                'vmetrics': vmetrics_default,
                # 'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': (0, 0, 1)}, 
                #'features': ["rvrn", "ccmp", "liga", "locl", "mark", "mkmk", "rlig"],
                #'features_remove': ["rlig"], 
                'variable': True,
                'static': True,
    },
    'Greek': {  
                'glyphs_encoded': set( list([x for x in range(0x0370, 0x03FF)])),  #['U+0370-03FF']
                'glyphs_unencoded': set(glyphs_unencoded_basic),
                'vmetrics': vmetrics_default,
                # 'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': (0, 0, 1)}, 
                #'features': ["rvrn", "ccmp", "liga", "locl", "mark", "mkmk", "rlig"],
                #'features_remove': ["rlig"], 
                'variable': True,
                'static': True,
    },
    'Cyrillic': {  
                'glyphs_encoded': set( list([x for x in range(0x400, 0x052F)])),  #['U+0400-052F']
                'glyphs_unencoded': set(glyphs_unencoded_basic),
                'vmetrics': vmetrics_default,
                # 'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': (0, 0, 1)}, 
                #'features': ["rvrn", "ccmp", "liga", "locl", "mark", "mkmk", "rlig"],
                #'features_remove': ["rlig"], 
                'variable': True,
                'static': True,
    },
    'Arabic': {  
                'glyphs_encoded': set( list([x for x in range(0x0600, 0x0700)] + 
                                            [x for x in range(0x0750, 0x0780)] +
                                            [x for x in range(0x08A0, 0x08FF)] +
                                            [x for x in range(0xFB50, 0xFE00)] +
                                            [x for x in range(0xFE70, 0xFF00)]
                                            )),  #['U+0600-06FF', 'U+0750-077F', 'U+08A0-08FE', 'U+FB50-FDFF', 'U+FE70-FEFF']
                'glyphs_unencoded': set(glyphs_unencoded_basic),
                'vmetrics': vmetrics_default,
                #'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': None}, #without Width and Italics, because Arabic don't have Italics and Condensed are not designed, yet.
                'axes': {'opsz': (10, 20, 20), 'wght': (300, 300, 700), 'ital': None}, #without Width and Italics, because Arabic don't have Italics and Condensed are not designed, yet.
                #'axes': {'opsz': None, 'wght': (300, 300, 700), 'ital': None},
                'variable': True,
                'static': True,
    },
    # Persian

    'Farsi': {  
                'glyphs_encoded': set( list([x for x in range(0x0600, 0x0700)] + 
                                            [x for x in range(0x0750, 0x0780)] +
                                            [x for x in range(0x08A0, 0x08FF)] +
                                            [x for x in range(0xFB50, 0xFE00)] +
                                            [x for x in range(0xFE70, 0xFF00)]
                                            )),  #['U+0600-06FF', 'U+0750-077F', 'U+08A0-08FE', 'U+FB50-FDFF', 'U+FE70-FEFF']
                'glyphs_unencoded': set(glyphs_unencoded_basic),
                'vmetrics': vmetrics_default,
                #'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': None}, #without Width and Italics, because Arabic don't have Italics and Condensed are not designed, yet.
                'axes': {'opsz': (10, 20, 20), 'wght': (300, 300, 700), 'ital': None}, #without Width and Italics, because Arabic don't have Italics and Condensed are not designed, yet.
                #'axes': {'opsz': None, 'wght': (300, 300, 700), 'ital': None},
                'variable': True,
                'static': True,
                'features_remove': ["ss10"], # remove stylistic set for persian, not needed, because we map the persian glyphs to arabic unicodes.
                'modFunc': make_persian_default_arabic,
                'folders': ['TTF_WEB','VAR_WEB'],  # Subsets für Web Fonts
    },
    'Latin Extended': {  
                'glyphs_encoded': latn_extended_unicodes,  
                'glyphs_unencoded': set(glyphs_unencoded_basic),
                'vmetrics': vmetrics_default,
                # 'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': (0, 0, 1)}, 
                #'features': ["rvrn", "ccmp", "liga", "locl", "mark", "mkmk", "rlig"],
                #'features_remove': ["rlig"], 
                'variable': True,
                'static': True,
    },
}

# We need a second loop, because different subsets for desktop and web, but same script name
get_subsets_2 = {
    'Farsi': {  
                'glyphs_encoded': '*', # 2025/06/18 DW will all Zeichen in Farsi Fonts für Desktop
                'glyphs_unencoded': '*',
                'vmetrics': vmetrics_default,
                #'axes': {'opsz': (10, 20, 20), 'wdth': None, 'wght': (300, 300, 700), 'ital': None}, #without Width and Italics, because Arabic don't have Italics and Condensed are not designed, yet.
                'axes': {'opsz': (10, 20, 20), 'wght': (300, 300, 700), 'ital': None}, #without Width and Italics, because Arabic don't have Italics and Condensed are not designed, yet.
                #'axes': {'opsz': None, 'wght': (300, 300, 700), 'ital': None},
                'variable': True,
                'static': True,
                'features_remove': ["ss10"], # remove stylistic set for persian, not needed, because we map the persian glyphs to arabic unicodes.
                'modFunc': make_persian_default_arabic,
                'folders': ['OTF', 'TTF_DESKTOP', 'VAR_DESKTOP'], # Kein Subset für Desktop Fonts
    },
}

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

#     return font_obj





def fix_recalcAvgCharWidth(font_obj):
    font_obj["OS/2"].recalcAvgCharWidth(font_obj)


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


def rename_font(dir_path, filename, subset_info, script, name_extention_before=None, name_extention_after=None, skip=()):
    if name_extention_before is None and name_extention_after is None:
        return None, None

    input_path = os.path.join(dir_path, filename)
    font_obj = TTFont(os.path.join(dir_path, filename))

    #skip unnecessary fonts (discussed with Ivo January 16, 2024):
    if subset_info.get('axes', None):
        coords_wdth = subset_info['axes'].get('wdth', False)
        coords_ital = subset_info['axes'].get('ital', False)

        if coords_wdth is None:
            # skip all condensed fonts
            if font_obj['OS/2'].usWidthClass != 5:
                skip.add('skip')

        if coords_ital is None:
            # skip all italic fonts
            if font_obj['post'].italicAngle != 0:
                skip.add('skip')

    if 'skip' in skip:
        return None, None

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


def subset_fonts(   font_obj, 
                    glyphs_encoded=[0x0041, 0x004C, 0x004C, 0x0049], 
                    glyphs_unencoded=['.notdef', '.null', 'null', 'NULL'], 
                    layout_features=None, 
                    layout_features_remove=None):

    opts = subset.Options()
    opts.name_IDs = ["*"]
    opts.name_legacy = True
    opts.name_languages = ["*"]
    print('opts.layout_features: ', opts.layout_features)
    #opts.layout_features = ["*"]
    if layout_features is not None:
        opts.layout_features = layout_features
    features_list_temp = opts.layout_features.copy()
    if layout_features_remove:
        for fea_tag in layout_features_remove:
            if fea_tag in features_list_temp:
                features_list_temp.remove(fea_tag)
    opts.layout_features = features_list_temp
    print('opts.layout_features: ', opts.layout_features)
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


def fix_fs_selection_wws(font_obj):
    name_table_obj = font_obj['name']
    name_id_21 = name_table_obj.getDebugName(21)
    name_id_22 = name_table_obj.getDebugName(22)

    if name_id_21 is None and name_id_22 is None:
        fs_selection = font_obj["OS/2"].fsSelection
        fs_selection |= 1 << 8
        font_obj["OS/2"].fsSelection = fs_selection


def remove_var_table_for_static_fonts(font_obj):
    if 'gvar' not in font_obj:
        for table in {'fvar', 'STAT', 'avar'}:
            if table in font_obj:
                del font_obj[table]
                print('Removed table: ', table)

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


def fix_zero_width_characters(font_obj):
    # unicode FEFF zerowidthnobreakspace should have a width of 0.
    # same for NULL
    #glyphset = font_obj.getGlyphSet()

    #for glyph_name in {'uniFEFF', 'NULL'}:
    #    glyph = glyphset[glyph_name]
    #    print('glyph: ', glyph)
    #    print('glyph.width: ', glyph.width)
    #    print('Changing glyph width: ', glyph_name, glyph.width, 0)
    #    glyph.width = 0
    return


def fix_missing_NID16_17(font_obj):
    has16 = False
    has17 = False
    name_table = font_obj['name']
    for rec in name_table.names:
        if rec.nameID == 16:
            has16 = True
        if rec.nameID == 17:
            has17 = True
    if has16 and has17:
        print("Font has name ID 16 and 17")
        return

    if not has16:
        name_table.setName(name_table.getDebugName(1), 16, 3, 1, 0x409)
    if not has17:
        name_table.setName(name_table.getDebugName(2), 17, 3, 1, 0x409)


def set_codePageRanges_latin1(font_obj):
    # set bit 0 (=Latin1) of ulCodePageRange1.
    OS2 = font_obj["OS/2"]
    cpl1, cpl2 = OS2.ulCodePageRange1, OS2.ulCodePageRange2
    cpl1 |= 1 << 0
    OS2.ulCodePageRange1 = cpl1


def adjust_vertical_Metrics(font_obj, vmetrics):
    typo_ascender = vmetrics['typo_ascender']
    typo_descender = vmetrics['typo_descender']
    typo_linegap = vmetrics['typo_linegap']

    win_ascent = vmetrics['win_ascent']
    win_descent = vmetrics['win_descent']
    
    hhea_ascent = vmetrics['hhea_ascent']
    hhea_descent = vmetrics['hhea_descent']
    hhea_linegap = vmetrics['hhea_linegap']

    OS2 = font_obj["OS/2"]
    if OS2.sTypoAscender != typo_ascender:
        OS2.sTypoAscender = typo_ascender
    if OS2.sTypoAscender != typo_descender:
        OS2.sTypoDescender = typo_descender
    if OS2.sTypoLineGap != typo_linegap:
        OS2.sTypoLineGap = typo_linegap

    if OS2.usWinAscent != win_ascent:
        OS2.usWinAscent = win_ascent
    if OS2.usWinDescent != win_descent:
        OS2.usWinDescent = win_descent

    hhea = font_obj["hhea"]
    if hhea.ascent != hhea_ascent:
        hhea.ascent = hhea_ascent
    if hhea.descent != hhea_descent:
        hhea.descent = hhea_descent
    if hhea.lineGap != hhea_linegap:
        hhea.lineGap = hhea_linegap



def fix_font(font_obj, font_path):

    #font_obj = TTFont(font_path)

    remove_var_table_for_static_fonts(font_obj)
    fix_fs_selection(font_obj)
    fix_mac_style(font_obj)
    fix_fs_selection_wws(font_obj)
    fix_hinted_font(font_obj)
    if 'gvar' in font_obj:
        fix_unhinted_font(font_obj)
    fix_bad_version(font_obj)
    #fix_zero_width_characters(font_obj) This is better to fix within Glyphsapp by using 'exclude' in the transform customer parameter

    #fix_missing_NID16_17(font_obj)
    #update_version(font_obj, version=0.90)
    #change_font_embedding(font_obj, level='editable embedding')
    #remove_mac_names(font_obj)
    # Christoph wünscht explizit Mac names. 
    # Darum werden die in der nächsten Zeile erstellt, basierend auf den Windows names.
    # create_mac_names(font_obj)
    fix_cff_names(font_obj)
    add_dummy_dsig(font_obj)

    return font_obj


def fix_font_2(font_obj):
    fix_recalcAvgCharWidth(font_obj)
    return font_obj


def run_post_script(path, folder):
    for filename in os.listdir(path):
        print('subset filename: ', filename)
        full_path = os.path.join(path, filename)
        print("PATH: {}".format(full_path))
        suffix = filename.split('.')[-1]


        if suffix.lower() in font_suffixes:
            print("\tIt's a font file.")
            for get_subset in [get_subsets, get_subsets_2]:
                for script in get_subset:
                    subset_info = get_subset[script]
                    f = subset_info.get('folders', None)
                    if f is not None and folder not in f:
                        continue

                    skip = set()
                    for key in ('variable', 'static'):
                        print('key: ', key)
                        value  = subset_info.get(key, None)
                        print('value: ', value)
                        if not value:
                            skip.add(key)

                    font_obj, font_path = rename_font(path, filename, subset_info, script, name_extention_after=script, skip=skip)
                    if None in (font_obj, font_path):
                        continue
                    
                    modFunc = subset_info.get('modFunc', None)
                    if modFunc:
                        # must be before subsetting the font.
                        modFunc(font_obj)

                    if subset_info['glyphs_encoded'] == '*' and subset_info['glyphs_unencoded'] == '*':
                        pass
                    else:
                        font_obj = subset_fonts(font_obj, 
                            glyphs_encoded=subset_info['glyphs_encoded'], 
                            glyphs_unencoded=subset_info['glyphs_unencoded'],
                            layout_features=subset_info.get('features', None),
                            layout_features_remove=subset_info.get('features_remove', None),
                            )
                    
                    if subset_info.get('vmetrics', None):
                        adjust_vertical_Metrics(font_obj, subset_info['vmetrics'])
                    fix_font(font_obj, font_path)
                    
                    if subset_info.get('axes', None) and 'fvar' in font_obj:
                        coords = subset_info['axes']
                        font_obj = instancer.instantiateVariableFont(font_obj, coords)

                    if subset_info.get('drop_axes', None) and 'fvar' in font_obj:
                        coords = subset_info['drop_axes']
                        font_obj = instancer.instantiateVariableFont(font_obj, coords)

                    fix_font_2(font_obj)

                    print('font_path: ', font_path)
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
            run_post_script(root, folder)


if __name__ == "__main__":
    main()



