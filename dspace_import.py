#!/usr/bin/env python3
# Importerar 2023 SLU studenters och PhD kursplaner, kurstillfällen samt utbildningsplaner i DSpace test- eller målsystem.
# Metadata i Dublin Core format. 
# Importen sker iterativt samt loggas i courseimport.log. Handles är samlingarnas. Unk är en sänka för enhetsnummer med okända arkivbildare.
# Utbildningsplaners handles är hårdkodade eftersom de är unika samtidigt som arkivbildaren ua också har kurser.

import argparse
import logging
import pandas as pd
import os
import subprocess

logging.basicConfig(filename='courseimport.log', filemode='w', level=logging.DEBUG)

def simparch_upload(email, simparcmainpath, dspacemainpath, target, ctype, creator):
   
   # En 2023 creator lista med respektive handles.
   crlist = pd.read_table('creators_handles.tsv')
   dspacebinpath = os.path.join(dspacemainpath, 'bin', 'dspace')

   if creator == ' ':
      clist = sorted(os.listdir(simparcmainpath))
      ('Creators: ', clist)
      dstcrpaths = []
      for cr in clist:
         if ctype == ' ':
            dstcrpaths.append(os.path.join(simparcmainpath, cr, 'kursplaner_'+cr))
         elif ctype == 'utbildningsplaner':
            dstcrpaths = [os.path.join(simparcmainpath, 'ua', 'utbildningsplaner_ua')]
   else:
      dstcrpaths = [os.path.join(simparcmainpath, creator, 'kursplaner_'+creator)]
   
   for c in sorted(dstcrpaths):
      cspl = os.path.basename(c).split('_')
      logging.info('Arkivbildare: '+str(cspl))
      mapfilepath = os.path.join(c, 'mapfile_' + cspl[1])

      if target == 'test':
         if ctype == ' ':
            handle = crlist[crlist['creator'] == cspl[1]]['test_handle'].values[0]
         elif ctype == 'utbildningsplaner':
            handle = '123456789/500'
      elif target == 'mål':
         if ctype == ' ':
            handle = crlist[crlist['creator'] == cspl[1]]['mål_handle'].values[0]
         elif ctype == 'utbildningsplaner':
            handle = '20.500.12703/4128'
      else:
         print('Välj först DSpace system.')
         break
      logging.info('Arkivbildare: '+ str(handle))
      dspaceargs = [dspacebinpath, 'import', '-a', '-e', email, '-c', handle,'-s', c, '-m', mapfilepath]
      logging.info(dspaceargs)
      subprocess.run(dspaceargs)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='dspace_import.py',
                    description='Tar en simparch folderstruktur för kursplaner och importerar till respektive arkivbildare.', 
                    epilog='Argumenten är sudo python3 dspace_import.py <e-post DSpace-admin> <arkivkatalog> <sökväg till DSpace> <system> [dokumenttyp] [arkivbildare].')
    parser.add_argument('email', help='En DSpace admin emailadress.')
    parser.add_argument('fpath', help='Foldern där arkivstrukturen hämtas.')
    parser.add_argument('dpath', help='Foldern där DSpace finns.')
    parser.add_argument('target', help='DSpace system: test/mål.')
    parser.add_argument('ctype', help='Option utbildningsplaner för att importera utbildningsplaner.', nargs='?', const=' ', default=' ')
    parser.add_argument('creator', help='Option att testa på en enstaka arkivbildare.', nargs='?', const=' ', default=' ')
    args = parser.parse_args()
    logging.info(args)
    simparch_upload(args.email, args.fpath, args.dpath, args.target,args.ctype, args.creator)
