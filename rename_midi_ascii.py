import os
import re

def ascii_filename(name):
    # Replace accented and special characters with closest ASCII equivalent
    # Remove anything not A-Za-z0-9._-
    name = re.sub(r'[éèêë]', 'e', name)
    name = re.sub(r'[áàâä]', 'a', name)
    name = re.sub(r'[íìîï]', 'i', name)
    name = re.sub(r'[óòôö]', 'o', name)
    name = re.sub(r'[úùûü]', 'u', name)
    name = re.sub(r'[ç]', 'c', name)
    name = re.sub(r'[ñ]', 'n', name)
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', name)
    return name

midi_dir = r'D:\MyProject\Verdi\Midi'
for root, dirs, files in os.walk(midi_dir):
    for fname in files:
        if fname.lower().endswith('.mid'):
            new_fname = ascii_filename(fname)
            if new_fname != fname:
                src = os.path.join(root, fname)
                dst = os.path.join(root, new_fname)
                print(f'Renaming: {src} -> {dst}')
                os.rename(src, dst)
print('Done.')
