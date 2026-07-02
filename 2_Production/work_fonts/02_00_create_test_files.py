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

FOLDERS = ['xOTF', 'xTTF', 'xVAR', 'VAR_DESKTOP', 'VAR_WEB']
DIR = os.path.dirname(__file__)


def create_dir_origin(DIR, folder_name):
    DIR_orig = os.path.join(DIR, folder_name)
    i = 1
    # Create directory
    if not os.path.exists(DIR_orig):
        # Create target Directory
        os.mkdir(DIR_orig)
        print("Directory " , DIR_orig ,  " Created ") 
    else:
        create_dir_origin(DIR, f'{folder_name}{i}' )
        i += 1
        print("Directory " , DIR_orig ,  " already exists")

    return DIR_orig


def get_fonts(path):
    fonts = []
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        suffix = filename.split('.')[-1]

        if suffix.lower() in font_suffixes:
            fonts.append(TTFont(full_path))
    return fonts


def run_quality_tools(path, loglevel='WARN'):
    '''
    Create test files for quality assurence.
    '''

    #print('path: ', path)
    #with patch('argparse._sys.argv', ['fontbakery', 'check-fontwerk', f"{path}/*[ot]tf", '--loglevel', loglevel, '--ghmarkdown', f'{path}/fontbakery_{loglevel}_report.md']):
    #    fontbakery_main()

    #call(['fontbakery', 'check-fontwerk', f"{path}/*[ot]tf", '-l', loglevel, '--ghmarkdown', f'{path}/fontbakery_{loglevel}_report.md'])
    call(['fontbakery', 'check-fontwerk', f'{path}/*[ot]tf', '-l', loglevel, '--html', f'{path}/fontbakery_{loglevel}_report.html'])

    
    #from gftools.gftools-qa
    #qa = FontQA(ttfonts, out=args.out)
    '''
    print('path: ', path)
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        suffix = filename.split('.')[-1]

        if suffix.lower() in font_suffixes:
            call(['gftools', 'qa', '--fonts', f"{path}", '--browser-previews']) # '--plot-glyphs', '-o', f'{path}'
    '''

    # from gftools.html import HtmlProof, HtmlDiff
    # fonts = get_fonts(path)
    # print('[f.reader.file.name for f in fonts]: ', [f.reader.file.name for f in fonts])

    # out = os.path.join(path, "browser_previews")
    # mkdir(out)
    # html = HtmlProof(
    #     out=out,
    #     fonts=[f.reader.file.name for f in fonts]
    # )
    # html.build_pages(["waterfall.html", "text.html"])
    # html.build_pages(["glyphs.html"], pt_size=16)
    #html.save_imgs()



def main(args=None):
    for root, dirs, files in os.walk(DIR):
        path, folder = os.path.split(root)
        if folder in FOLDERS:
            print('root: ', root)
            #try:
            run_quality_tools(root)
            #except:
                #print('Error: Cannot create test files for: ', root)

if __name__ == "__main__":
    main()



