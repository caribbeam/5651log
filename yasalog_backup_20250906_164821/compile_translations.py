#!/usr/bin/env python
import os
import polib

def compile_po_to_mo(po_file_path, mo_file_path):
    """Compile .po file to .mo file using polib"""
    try:
        po = polib.pofile(po_file_path)
        po.save_as_mofile(mo_file_path)
        print(f"Compiled {po_file_path} to {mo_file_path}")
    except Exception as e:
        print(f"Error compiling {po_file_path}: {e}")

def main():
    # Compile Turkish translations
    tr_po = "locale/tr/LC_MESSAGES/django.po"
    tr_mo = "locale/tr/LC_MESSAGES/django.mo"
    
    if os.path.exists(tr_po):
        compile_po_to_mo(tr_po, tr_mo)
    else:
        print(f"PO file not found: {tr_po}")
    
    # Compile English translations
    en_po = "locale/en/LC_MESSAGES/django.po"
    en_mo = "locale/en/LC_MESSAGES/django.mo"
    
    if os.path.exists(en_po):
        compile_po_to_mo(en_po, en_mo)
    else:
        print(f"PO file not found: {en_po}")

if __name__ == "__main__":
    main() 