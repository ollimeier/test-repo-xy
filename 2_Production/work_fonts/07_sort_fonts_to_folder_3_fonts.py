#!/usr/bin/env python3
"""
Script to create trial and web fonts.
by Olli Meier.
"""

import os
import shutil

from fontTools.ttLib import TTFont
from fontTools import subset

DIR = os.path.dirname(__file__)

web_base_format = 'TTF_WEB' # OTF or TTF_WEB
font_formats = {'ttf', 'otf', 'woff', 'woff2'}

FOLDERS = {
    '3_Fonts/ONLY_FONTWERKCOM/COMPLETE/STATIC': f'2_Production/work_fonts/ONLY_FONTWERKCOM/COMPLETE/{web_base_format}',
    '3_Fonts/ONLY_FONTWERKCOM/COMPLETE/VAR': '2_Production/work_fonts/ONLY_FONTWERKCOM/COMPLETE/VAR_WEB',
    '3_Fonts/ONLY_FONTWERKCOM/SUBSET/STATIC': f'2_Production/work_fonts/ONLY_FONTWERKCOM/SUBSET/{web_base_format}',
    '3_Fonts/ONLY_FONTWERKCOM/SUBSET/VAR': '2_Production/work_fonts/ONLY_FONTWERKCOM/SUBSET/VAR_WEB',

    '3_Fonts/PRODUCTS/DESKTOP/STATIC/OTF': '2_Production/work_fonts/OTF',
    '3_Fonts/PRODUCTS/DESKTOP/STATIC/TTF': '2_Production/work_fonts/TTF_DESKTOP',
    '3_Fonts/PRODUCTS/DESKTOP/VAR/TTF': '2_Production/work_fonts/VAR_DESKTOP',
    #'3_Fonts/PRODUCTS/DESKTOP/VAR/OTF': '2_Production/work_fonts/',
    '3_Fonts/PRODUCTS/WEB/STATIC': f'2_Production/work_fonts/WEB/{web_base_format}',
    '3_Fonts/PRODUCTS/WEB/VAR': '2_Production/work_fonts/WEB/VAR_WEB',

    '3_Fonts/TRIALS/DESKTOP/STATIC/OTF': '2_Production/work_fonts/_TRIALS/OTF',
    '3_Fonts/TRIALS/DESKTOP/STATIC/TTF': '2_Production/work_fonts/_TRIALS/TTF_DESKTOP',
    '3_Fonts/TRIALS/DESKTOP/VAR/TTF': '2_Production/work_fonts/_TRIALS/VAR_DESKTOP',
    #'3_Fonts/TRIALS/DESKTOP/VAR/OTF': '2_Production/work_fonts/',
    '3_Fonts/TRIALS/WEB/STATIC': f'2_Production/work_fonts/_TRIALS/WEB/{web_base_format}',
    '3_Fonts/TRIALS/WEB/VAR': '2_Production/work_fonts/_TRIALS/WEB/VAR_WEB',
}


def get_project_folder(path):
    project_folder_path = None
    base_path, folder_name = os.path.split(path)
    fonts_folder = os.path.join(base_path, '3_Fonts')
    production_folder = os.path.join(base_path, '2_Production')
    print('base_path: ', base_path)
    print('fonts_folder: ', fonts_folder)
    print('production_folder: ', production_folder)
    if os.path.exists(fonts_folder) and os.path.exists(production_folder):
        # most likley it's the prjects folder if both folder exists.
        project_folder_path = base_path
    else:
        project_folder_path = get_project_folder(base_path)

    return project_folder_path


def main(args=None):
    projekt_folder = get_project_folder(DIR)
    print('Project: ', projekt_folder)


    for fonts_save_path in FOLDERS:
        path_new = os.path.join(projekt_folder, fonts_save_path)
        if os.path.exists(path_new):
            print('Path exists already. Please make sure to remove/save the data before running this script.')
            return

        path_orig = os.path.join(projekt_folder, FOLDERS[fonts_save_path])
        if not os.path.exists(path_orig):
            print(f"Path: {path_orig} does not exist. Please investigate.")
            continue

        shutil.copytree(path_orig, path_new)
        print(f"Done: Files copied: ")
        print(f"\tfrom\t{path_orig}")
        print(f"\tto\t\t{path_new}")



if __name__ == "__main__":
    main()



