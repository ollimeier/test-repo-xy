#!/usr/bin/env python3
"""

Post production script originally by Eigi (Andreas Eigendorf)
modified by Olli Meier (2023/12/13).

"""

from __future__ import annotations
import logging
import os
import sys
import traceback
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from typing import Dict, Tuple

from fontTools import __version__ as ftVersion
from fontTools.ttLib import TTFont, TTLibError
from fontTools.ttLib.tables._k_e_r_n import KernTable_format_0, table__k_e_r_n
from unicodedata2 import category

try:
    from fontToolsTools import __version__
except Exception:
    __version__ = 'UNKOWN'

log = logging.getLogger(__name__)

MAX_KERN = 10919

font_suffixes = {'ttf'}
FOLDERS = ['TTF', 'TTF_DESKTOP']
DIR = os.path.dirname(__file__)


DEFAULT_KERNING_GLYPHS = (   
    '''AÁĂǍÂÄÀĀĄÅǺÃÆǼBCĆČÇĈĊDÐĎĐEÉĔĚÊËĖÈĒĘFGǴĞĜĢĠHĦĤIÍĬǏÎÏİÌĪĮĨĲJĴ'''
    '''aáăǎâäàāąåǻãæǽbcćčçĉċdðďđeéĕěêëėèēęfgǵğĝģġhħĥıiíĭǐîïìīįĩĳjĵ'''
    '''KĶLĹĽĻĿŁMNŃŇŅŊÑOÓŎǑÔÖÒŐŌǪØǾÕŒPÞQRŔŘŖSŚŠŞŜȘẞTŦŤŢȚUÚŬǓÛÜǗǙǛǕÙŰŪŲŮŨ'''
    '''kķlĺľļŀłmnńňņŋñoóŏǒôöòőōǫøǿõœpþqrŕřŗsśšşŝșßtŧťţțuúŭǔûüǘǚǜǖùűūųůũ'''
    '''VWẂŴẄẀXYÝŶŸỲZŹŽŻ'''
    '''vwẃŵẅẁxyýŷÿỳzźžż'''
    '''АБВГЃҐДЕЀЁЖЗИЙЍКЌЛМНОПРСТУЎФХЧЦШЩЏЬЪЫЉЊЅЄЭІЇЈЋЮЯЂѢѲѴҒҖҚҜҢҮҲҸҺӀӘӢӨӮ'''
    '''абвгѓґдеѐёжзийѝкќлмнопрстуўфхчцшщџьъыљњѕєэіїјћюяђѣѳѵғҗқҝңүҳҹһӏәӣөӯ'''
    '''.,:;?¿*‽„“”‘’‛«»‹›'"'''
    '''0123456789''')

def getFlatKerning(font:TTFont) -> Dict[Tuple[str, str], int]:
    kerningPairs = {}
    if font.has_key("GPOS"):
        GPOS = font["GPOS"]
        kernLookupIndexes = set()
        for featureRec in GPOS.table.FeatureList.FeatureRecord:
            if featureRec.FeatureTag == "kern":
                kernLookupIndexes |= set(featureRec.Feature.LookupListIndex)
        for lookup in [
            GPOS.table.LookupList.Lookup[i] for i in sorted(kernLookupIndexes)
        ]:
            if lookup.LookupType == 2:  # Pair adjustment
                for lookupSubtable in lookup.SubTable:
                    log.debug("=== new subtable ===")

                    if lookupSubtable.Format == 1:  # glyph to glyph kerning
                        for i, glyph_1 in enumerate(lookupSubtable.Coverage.glyphs):
                            pair = lookupSubtable.PairSet[i]
                            for valueRec in pair.PairValueRecord:
                                glyph_2 = valueRec.SecondGlyph
                                value = valueRec.Value1.XAdvance
                                key = (glyph_1, glyph_2)
                                if key not in kerningPairs:
                                    kerningPairs[(glyph_1, glyph_2)] = value

                    elif lookupSubtable.Format == 2:  # class kerning
                        # get first classes
                        coverage = list(lookupSubtable.Coverage.glyphs)
                        firstClasses = []
                        for i in range(lookupSubtable.Class1Count):
                            firstClasses.append([])
                        for (
                            glyphName,
                            index,
                        ) in lookupSubtable.ClassDef1.classDefs.items():
                            firstClasses[index].append(glyphName)
                            coverage.remove(glyphName)
                        firstClasses[0] = list(coverage)
                        # get second classes
                        secondClasses = []
                        for i in range(lookupSubtable.Class2Count):
                            secondClasses.append([])
                        for (
                            glyphName,
                            index,
                        ) in lookupSubtable.ClassDef2.classDefs.items():
                            secondClasses[index].append(glyphName)
                        # expand class kerning to simple glyph to glyph kerning
                        for firstIndex, class1rec in enumerate(
                            lookupSubtable.Class1Record
                        ):
                            firstClass = firstClasses[firstIndex]
                            for secondIndex, class2rec in enumerate(
                                class1rec.Class2Record
                            ):
                                secondClass = secondClasses[secondIndex]
                                value = class2rec.Value1.XAdvance
                                if value:
                                    for glyph_1 in firstClass:
                                        for glyph_2 in secondClass:
                                            key = (glyph_1, glyph_2)
                                            if key not in kerningPairs:
                                                kerningPairs[(glyph_1, glyph_2)] = value
                    else:
                        log.error("Unhandled SubTable Format: %r", lookup.LookupType)
            elif lookup.LookupType == 9:  # 	Extension Lookup
                for lookupSubtable in lookup.SubTable:
                    if lookupSubtable.LookupType == 9:
                        extSubTable = lookupSubtable.ExtSubTable
                        if extSubTable.Format == 1:  # glyph to glyph kerning
                            for i, glyph_1 in enumerate(extSubTable.Coverage.glyphs):
                                pair = extSubTable.PairSet[i]
                                for valueRec in pair.PairValueRecord:
                                    glyph_2 = valueRec.SecondGlyph
                                    value = valueRec.Value1.XAdvance
                                    key = (glyph_1, glyph_2)
                                    if key not in kerningPairs:
                                        kerningPairs[(glyph_1, glyph_2)] = value
                        elif extSubTable.Format == 2:  # class kerning
                            # get first classes
                            coverage = list(extSubTable.Coverage.glyphs)
                            firstClasses = []
                            for i in range(extSubTable.Class1Count):
                                firstClasses.append([])
                            for (
                                glyphName,
                                index,
                            ) in extSubTable.ClassDef1.classDefs.items():
                                firstClasses[index].append(glyphName)
                                coverage.remove(glyphName)
                            firstClasses[0] = list(coverage)
                            # get second classes
                            secondClasses = []
                            for i in range(extSubTable.Class2Count):
                                secondClasses.append([])
                            for (
                                glyphName,
                                index,
                            ) in extSubTable.ClassDef2.classDefs.items():
                                secondClasses[index].append(glyphName)
                            # expand class kerning to simple glyph to glyph kerning
                            for firstIndex, class1rec in enumerate(
                                extSubTable.Class1Record
                            ):
                                firstClass = firstClasses[firstIndex]
                                for secondIndex, class2rec in enumerate(
                                    class1rec.Class2Record
                                ):
                                    secondClass = secondClasses[secondIndex]
                                    value = class2rec.Value1.XAdvance
                                    if value:
                                        for glyph_1 in firstClass:
                                            for glyph_2 in secondClass:
                                                key = (glyph_1, glyph_2)
                                                if key not in kerningPairs:
                                                    kerningPairs[
                                                        (glyph_1, glyph_2)
                                                    ] = value
                    else:
                        log.error(
                            "Unhandled ExtensionLookupType: %r",
                            lookupSubtable.ExtensionLookupType,
                        )
            else:
                log.error("Unhandled LookupType: %r", lookup.LookupType)
    else:
        log.error("No GPOS table found")
    return kerningPairs


def get_most_important_characters_for_kern(font_obj):
    if font_obj is None:
        return DEFAULT_KERNING_GLYPHS
    
    collect_unicodes = set(font_obj["cmap"].getBestCmap())

    # Ll = Letter Lowercase
    # Lu = Letter Uppercase
    # Ps = Punctuation Open
    # Pe = Punctuation Close
    collect_chr = set()
    for uni in collect_unicodes:
        c = chr(uni)
        if category(c) in ['Ll', 'Lu', 'Ps', 'Pe']:
            collect_chr.add(c)
    return ''.join(sorted(collect_chr))


def get_set_of_unicode_values(str):
    kern_chr = set()
    for c in str:
        try:
            kern_chr.add(ord(c))
        except Exception:
            print('Not a unicode character: ', c)
    return kern_chr    


def make_kern_table(font:TTFont):
    gpos_kern = getFlatKerning(font)
    if gpos_kern:
        cmap = font["cmap"].getBestCmap()
        encodedGlyphs = cmap.values()
        glyph_to_char = {v: chr(k) for k, v in cmap.items()}
        kerning = {}
        # remove kerning for unencoded glyphs
        print('START Kern Tabel Level 0: ', len(gpos_kern))
        print('\tRemoving kerning ...')
        print('\t\tunencoded glyphs')
        print('\t\tvalue below -5 or above +5')
        # Notiz für Eigi: 
        # Egänzt um positives Kerning 'or value >= 5'. 
        # Könnte wichtig sein bei z.B. Akzentbuchstaben wie /S /itilde
        for pair, value in gpos_kern.items():
            if pair[0] in encodedGlyphs and pair[1] in encodedGlyphs and (value <= -5 or value >= 5):
                kerning[pair] = value
        print('END Kern Tabel Level 0: ', len(kerning))

        if len(kerning) > MAX_KERN:
            print('START Kern Tabel Level 1: ', len(kerning))
            print('\tKeep most important kerning ...')
            _kerning = {}
            kern_chr = get_set_of_unicode_values(get_most_important_characters_for_kern(font))

            for pair, value in kerning.items():
                glyph_1 = glyph_to_char[pair[0]]
                glyph_2 = glyph_to_char[pair[1]]
                unicode_1 = ord(glyph_1)
                unicode_2 = ord(glyph_2)
                if unicode_1 in kern_chr and unicode_2 in kern_chr:
                    _kerning[pair] = value
            kerning = _kerning
            print('END Kern Tabel Level 1: ', len(kerning))

        if len(kerning) > MAX_KERN:
            print('START Kern Tabel Level 2: ', len(kerning))
            print('\tRemoving Kerning:')
            print(  '''\t\tcontrols and symbols\n'''
                    '''\t\tlowercase to uppercase\n'''
                    '''\t\tPunctuation to Punctuation\n'''
                    '''\t\tPunctuation and Separators\n''')
            _kerning = {}
            for pair, value in kerning.items():
                cat_0 = category(glyph_to_char[pair[0]])
                cat_1 = category(glyph_to_char[pair[1]])
                # controls and symbols
                if cat_0[0] in ("C", "S"):
                    continue
                if cat_1[0] in ("C", "S"):
                    continue
                # lowercase to uppercase
                if cat_0 == "Ll" and cat_1 == "Lu":
                    continue
                # Punctuation to Punctuation
                if cat_0[0] == "P" and cat_1[0] == "P":
                    continue
                # Punctuation and Separators
                if cat_0[0] in ("Z", "P") and cat_1[0] in ("Z", "P"):
                    continue
                _kerning[pair] = value
            kerning = _kerning
            print('END Kern Tabel Level 2: ', len(kerning))

        # remove Uppercase to uppercase Kerning.
        if len(kerning) > MAX_KERN:
            print('START Kern Tabel Level 3: ', len(kerning))
            print('\tRemoving Uppercase to Uppercase Kerning...')
            _kerning = {}
            for pair, value in kerning.items():
                cat_0 = category(glyph_to_char[pair[0]])
                cat_1 = category(glyph_to_char[pair[1]])
                # uppercase to uppercase
                if cat_0 == "Lu" and cat_1 == "Lu":
                    #skip uppercase to uppercase
                    continue
                _kerning[pair] = value
            kerning = _kerning
            print('END Kern Tabel Level 3: ', len(kerning))

        if len(kerning) > MAX_KERN:
            print('START Kern Tabel Level 4: ', len(kerning))
            print('\tKeep most important kerning minimum ...')
            _kerning = {}
            kern_chr = get_set_of_unicode_values(DEFAULT_KERNING_GLYPHS)

            for pair, value in kerning.items():
                glyph_1 = glyph_to_char[pair[0]]
                glyph_2 = glyph_to_char[pair[1]]
                unicode_1 = ord(glyph_1)
                unicode_2 = ord(glyph_2)
                if unicode_1 in kern_chr and unicode_2 in kern_chr:
                    _kerning[pair] = value

            kerning = _kerning
            print('END Kern Tabel Level 4: ', len(kerning))

        if len(kerning) > MAX_KERN:
            print('Kern Tabel Level 5: ', len(kerning))
            print('\tCut off all kerning above: ', MAX_KERN)
            _kerning = sorted([(v, k) for k, v in kerning.items()])
            kerning = {k: v for v, k in _kerning[:MAX_KERN]}

        kernTbl = table__k_e_r_n("kern")
        kernTbl.version = 0
        kernTbl.kernTables = []
        kernTbl.kernTables.append(KernTable_format_0())
        kernTbl.kernTables[0].coverage = 1
        kernTbl.kernTables[0].kernTable = kerning
        return kernTbl


def update_kern_table(font:TTFont):
    kernTbl = make_kern_table(font)
    if kernTbl:
        font["kern"] = kernTbl


def add_kern_table(font:TTFont):
    if "kern" not in font:
        update_kern_table(font)


def add_kern_table_cli(arguments=None):
    """Command line interface for add_kern_table."""
    # set up the parser
    parser = ArgumentParser(
        prog="addKernTable",
        description="Create a kern table from GPOS kern feature and add it to the font",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "font", type=str, help="Path to font, either OTF, TTF, WOFF or WOFF2"
    )
    # parse the arguments
    if not arguments:
        arguments = sys.argv[1:]
    args = parser.parse_args(arguments)
    returncode = 1
    sys.stdout.write(
        "\naddKernTable Ver: %s, FontTools Ver: %s\n" % (__version__, ftVersion)
    )
    # do the work
    if os.path.isfile(args.font):
        try:
            font = TTFont(args.font, lazy=False)
            sys.stdout.write('font "%s" loaded\n' % os.path.basename(args.font))
            if "GPOS" in font:
                kernTbl = make_kern_table(font)
                if kernTbl:
                    font["kern"] = kernTbl
                    sys.stdout.write('kern table generated for font "%s".\n' % os.path.basename(args.font))
                    font.save(args.font)
                    sys.stdout.write('font "%s" saved\n' % os.path.basename(args.font))
                    returncode = 0
                else:
                    sys.stderr.write('kern table generation failed for font "%s".\n' % os.path.basename(args.font))
            else:
                sys.stdout.write('font "%s" has no GPOS table, no kern table generated.\n' % os.path.basename(args.font))
                returncode = 0
            font.close()
        except TTLibError:
            sys.stderr.write(traceback.format_exc().splitlines()[-1])
    else:
        sys.stderr.write('font file not found: "%s"\n' % args.font)
    return returncode


def fix_font(dir_path, filename):
    font_path = os.path.join(dir_path, filename)
    font_obj = TTFont(font_path)

    if "GPOS" in font_obj:
        kernTbl = make_kern_table(font_obj)
        if kernTbl:
            font_obj["kern"] = kernTbl
            font_obj.save(font_path)
        font_obj.close()


def run_post_script(path):
    for filename in os.listdir(path):
        print('filename: ', filename)
        full_path = os.path.join(path, filename)
        print("PATH: {}".format(full_path))
        suffix = filename.split('.')[-1]

        if suffix.lower() in font_suffixes:
            fix_font(path, filename)
        else:
            print("\tIt's NOT a font file.")


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
