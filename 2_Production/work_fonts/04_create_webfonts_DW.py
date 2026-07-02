#!/usr/bin/env python3
"""
Script to create trial and web fonts.
by Olli Meier.
"""

import os
import shutil
from importlib.machinery import SourceFileLoader

from fontTools.ttLib import TTFont
from fontTools import ttLib
from fontTools import subset

#from glyphsets import codepoints # this is usually installed with gftools

FOLDERS = ['xOTF', 'TTF_WEB', 'xVAR', 'xVAR_DESKTOP', 'VAR_WEB']
DIR = os.path.dirname(__file__)

# fontwerk_spec_dir = f"{DIR.split('Fontwerk-Server')[0]}/Fontwerk-Server/Typefaces/specifications/"
# fontwerk_latin_trial_glyph_set_dict = codepoints.ReadNameList(f"{fontwerk_spec_dir}glyphsets/fontwerk-latin-trial_unique-glyphs.nam")

font_suffixes = {'ttf', 'otf'}

# trial_latin_glyphs_encoded =  fontwerk_latin_trial_glyph_set_dict['charset']
# trial_latin_glyphs_unencoded = fontwerk_latin_trial_glyph_set_dict['noCharcode']

# fontwerk_conditions = SourceFileLoader('fontwerk_conditions', f"{fontwerk_spec_dir}fontwerk_conditions.py").load_module()

def shorten_name(name, max_len=31):
    if len(name) <= max_len:
        return name

    if 'Italic' in name:
        name = name.replace('Italic', 'Ita')

        if len(name) > max_len:
            name = name.replace('Ita', 'It')

        name = shorten_name(name)

    if 'Headline' in name:
        name.replace('Headline', 'Head')

    if 'Extra' in name:
        name = name.replace('Extra', 'Ext')

        if len(name) > max_len:
            name = name.replace('Ext', 'X')

    return name


def loop_fonts(path):
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        suffix = filename.split('.')[-1]

        if suffix.lower() in font_suffixes:
            yield path, filename
        else:
            # skip: It's NOT a font file.
            continue


def create_trial_fonts(input_path, output_path, family_name=None):

    folder, file = os.path.split(output_path)  # noqa: F821

    opts = subset.Options()
    opts.name_IDs = ["*"]
    opts.name_legacy = True
    opts.name_languages = ["*"]
    opts.layout_features = ["*"]
    opts.recalc_timestamp = True
    opts.canonical_order = True
    opts.ignore_missing_glyphs = True
    opts.glyph_names = True
    # opts.obfuscate_names = True # this would be interesting for creating webfonts.
    # opts.flavor = None  # May be 'woff' or 'woff2'
    
    # for more options please see:
    # https://github.com/fonttools/fonttools/blob/31ba5e6b2428b088df6d0db029ac4e7d3d49bcd4/Lib/fontTools/subset/__init__.py#L2612

    subsetter = subset.Subsetter(options=opts)
    font_obj = subset.load_font(input_path, opts)

    update_name_table_trial(font_obj)

    subsetter.populate(glyphs=trial_latin_glyphs_unencoded, unicodes=trial_latin_glyphs_encoded)
    subsetter.subset(font_obj)


    if family_name is None:
        family_name = get_family_name(font_obj).replace('Trial', '').strip(' ')

    family_name_new = f'{family_name} Trial'


    filename_new = file.replace(family_name, family_name_new)

    if family_name.replace(' ', '') in file:
        filename_new = file.replace(family_name.replace(' ', ''), family_name_new.replace(' ', ''))

    if len(filename_new) > 31:
        filename_new = shorten_name(filename_new)

    output_path_trial = output_path.replace(file, filename_new)

    print('trial_path: ', output_path_trial)
    subset.save_font(font_obj, output_path_trial, opts)
    font_obj.close()

    # Keep in mind a different solution:
    # subset.main([fontpath, "--unicodes=U+0041,U+0028,U+0302,U+1D400,U+1D435", "--output-file=%s" % subsetpath])


def get_family_name(font_obj):
    name_table_obj = font_obj['name']

    for name_ID in [21, 16, 1]:
        fam_name = name_table_obj.getDebugName(name_ID)
        if fam_name is not None:
            return fam_name

    return None


def update_name_table_trial(font_obj, family_name=None):
    if family_name is None:
        family_name = get_family_name(font_obj)

    family_name_new = f'{family_name} Trial'
    
    for name_rec in font_obj['name'].names:
        name_id = name_rec.nameID
        name_str = f'{name_rec}'
        if name_id in [1, 3, 4, 6, 16, 21, 25]:
            if family_name in name_str:
                name_str_new = name_str.replace(family_name, family_name_new)
            else:
                if family_name.replace(' ', '') in name_str:
                    name_str_new = name_str.replace(family_name.replace(' ', ''), family_name_new.replace(' ', ''))

            if name_id in [3, 6]:
                # remove spaces
                name_str_new = name_str_new.replace(' ', '')

            name_rec.string = name_str_new

        if name_id == 10: # Description Text
            name_rec.string = fontwerk_conditions.trial["name table"][10]

        if name_id == 13: # License Text
            name_rec.string = fontwerk_conditions.trial["name table"][13]

    # TODO: remove instance postscript names
    #font_obj['name'].names = name_recs


def run_create_trial_fonts(DIR, folder):
    trial_dir = os.path.join(DIR, '_TRIALS')
    trial_dir_subfolder = os.path.join(DIR, '_TRIALS', folder)

    if not os.path.exists(trial_dir):
        os.mkdir(trial_dir)

    if not os.path.exists(trial_dir_subfolder):
        os.mkdir(trial_dir_subfolder)

    for path, filename in loop_fonts(os.path.join(DIR, folder)):
        input_path = os.path.join(path, filename)
        output_path = os.path.join(trial_dir_subfolder, filename)
        create_trial_fonts(input_path, output_path)


def run_create_webfonts(DIR, folder):
    trial_dir = os.path.join(DIR, 'WEB')
    trial_dir_subfolder = os.path.join(DIR, 'WEB', folder)

    if not os.path.exists(trial_dir):
        os.mkdir(trial_dir)

    if not os.path.exists(trial_dir_subfolder):
        os.mkdir(trial_dir_subfolder)

    for path, filename in loop_fonts(os.path.join(DIR, folder)):
        input_path = os.path.join(path, filename)
        output_path = os.path.join(trial_dir_subfolder, filename)
        create_webfonts(input_path, output_path)


def update_fvar_postscript_names(font_obj):
    '''
    This functions reduces the file size for web fonts by 
    removing all postscript instance names from fvar and name table.

    '''

    if 'fvar' not in font_obj:
        return

    ps_name_ids = set()
    for instance in font_obj['fvar'].instances:
        # first collect: instance.postscriptNameID

        if isinstance(instance.postscriptNameID, int):
            ps_name_ids.add(instance.postscriptNameID)

            # remove name id by using 0xFFFF
            instance.postscriptNameID = 0xFFFF

    name_table_obj = font_obj['name']

    for name_id in ps_name_ids:
        name_table_obj.removeNames(nameID=name_id)
        #print('Removing name ID: ', name_id)


def update_name_table_webfont(font_obj):
    # obfuscate names
    name_recs = []
    for name_rec in font_obj['name'].names:
        if name_rec.nameID in [1, 3, 4, 6]:
            name_rec.string = "  ".encode('utf_16_be') if name_rec.isUnicode() else "  "
        name_recs.append(name_rec)

    # TODO: remove instance postscript names
    font_obj['name'].names = name_recs


def update_cmap_table_webfont(font_obj):
    '''
    This functions reduces the file size for web fonts by 
    removing all unnecessary cmap subtables.

    cmap subtables to keep ((3, 1), (3, 10))
    '''

    if 'cmap' not in font_obj:
        return

    cmap = font_obj['cmap']
    cmap.tables = [t for t in cmap.tables if t.isUnicode() or t.isSymbol()]

    cmap.tables = [t for t in cmap.tables if t.format != 0]
    cmap.numSubTables = len(cmap.tables)


def update_post_table_webfont(font_obj):
    '''
    This functions reduces the file size for web fonts by 
    removing glyph postscript names.
    The code is basically a copy from 
    fonttools subsetter: option glyph_names = False

    '''

    post = ttLib.getTableClass('post')
    saved = post.decode_format_2_0
    post.decode_format_2_0 = post.decode_format_3_0
    f = font_obj['post']
    if f.formatType == 2.0:
        f.formatType = 3.0
    post.decode_format_2_0 = saved


def save_woff(input_path, output_path, format='woff2'):
    font_obj = TTFont(input_path)
    #update_name_table_webfont(font_obj) # DW will explizit keine obfuscated webfonts.
    update_post_table_webfont(font_obj)
    update_cmap_table_webfont(font_obj)
    update_fvar_postscript_names(font_obj)
    font_obj.flavor = format
    font_suffix = input_path.split('.')[-1]
    woff_path = output_path.replace('.{}'.format(font_suffix), f'.{format}')
    print('woff_path: ', woff_path)
    font_obj.save(woff_path)


def create_webfonts(input_path, output_path):
    save_woff(input_path, output_path)
    #save_woff(input_path, output_path, format='woff')


def main(args=None):

    for root, dirs, files in os.walk(DIR):
        path, folder = os.path.split(root)

        if any([True for x in ['_TRIALS', 'WEB', '_archive', '.idea'] if x in os.path.normpath(root).split(os.path.sep)]):
            # skip fonts in these folders.
            # will be created later.
            continue

        if folder in FOLDERS:
            print('root: ', root)
            run_create_webfonts(path, folder)



if __name__ == "__main__":
    main()



