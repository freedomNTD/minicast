"""Compile gettext catalogs without an external ``msgfmt`` binary.

Run directly to compile the default catalog::

    python build_i18n.py

or import :func:`compile_po_to_mo` from another tool (``setup.py`` imports it
for the ``compile_catalog`` command). The implementation mirrors CPython's
``Tools/i18n/msgfmt.py`` so it has no third-party dependencies.
"""

import os
import struct


def compile_po_to_mo(po_path, mo_path):
    """Compile a gettext ``.po`` catalog into a binary ``.mo`` file."""
    messages = _parse_po(po_path)
    _write_mo(mo_path, messages)


def _parse_po(po_path):
    with open(po_path, 'rb') as f:
        raw_lines = [ln.strip() for ln in f.readlines()]
    lines = [ln.decode('utf-8') for ln in raw_lines
             if ln and not ln.startswith(b'#')]

    messages = {}
    msgid = None
    msgstr = None
    section = None

    def store():
        nonlocal msgid, msgstr
        if msgid is not None:
            messages[msgid] = msgstr or ''
        msgid = msgstr = None

    for line in lines:
        if line.startswith('msgid '):
            if section == 'msgstr':
                store()
            section = 'msgid'
            msgid = _unescape(line[6:])
            msgstr = ''
        elif line.startswith('msgstr '):
            section = 'msgstr'
            msgstr = _unescape(line[7:])
        elif line.startswith('"') and line.endswith('"'):
            fragment = _unescape(line)
            if section == 'msgid':
                msgid += fragment
            elif section == 'msgstr':
                msgstr += fragment
        else:
            if section == 'msgstr':
                store()
                section = None
    store()
    return messages


def _unescape(value):
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return (value.replace('\\n', '\n')
                 .replace('\\t', '\t')
                 .replace('\\"', '"')
                 .replace("\\'", "'")
                 .replace('\\\\', '\\'))


def _write_mo(mo_path, messages):
    # The empty msgid "" maps to the catalog header (which carries the
    # charset). gettext decodes everything as ASCII unless that header declares
    # a charset, so the "" entry must be the first one in the file.
    keys = sorted(k for k in messages if k)
    all_keys = ([''] if '' in messages else []) + keys
    offsets = []
    ids = b''
    strs = b''
    for k in all_keys:
        v = messages.get(k, '')
        enc_k = k.encode('utf-8')
        enc_v = v.encode('utf-8')
        offsets.append((len(ids), len(enc_k), len(strs), len(enc_v)))
        ids += enc_k + b'\x00'
        strs += enc_v + b'\x00'

    # The original .mo format stores the offset table sorted by key string so
    # gettext can binary-search. We built ``ids`` already in sorted key order
    # (with "" forced first), so the table is already in the right order.
    keystart = 7 * 4 + 16 * len(all_keys)
    valuestart = keystart + len(ids)

    output = struct.pack(
        "Iiiiiii",
        0x950412de,             # magic
        0,                      # version
        len(all_keys),          # number of entries
        7 * 4,                  # offset of table with original strings
        7 * 4 + len(all_keys) * 8,  # offset of table with translation strings
        0, 0,                   # size and offset of hash table (unused)
    )
    # The .mo layout is two separate 8-byte-per-entry tables laid out
    # contiguously (original strings table first, then translations table),
    # followed by the string data. They must NOT be interleaved, or gettext's
    # independent seek pointers into each table will desync.
    for o1, o2, o3, o4 in offsets:
        output += struct.pack("ii", o2, keystart + o1)          # length, offset of original
    for o1, o2, o3, o4 in offsets:
        output += struct.pack("ii", o4, valuestart + o3)        # length, offset of translation
    output += ids
    output += strs

    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, 'wb') as f:
        f.write(output)


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    po = os.path.join(here, 'i18n', 'zh_CN', 'LC_MESSAGES', 'minicast.po')
    mo = os.path.join(here, 'i18n', 'zh_CN', 'LC_MESSAGES', 'minicast.mo')
    if not os.path.exists(po):
        raise SystemExit("catalog source not found: %s" % po)
    compile_po_to_mo(po, mo)
    print("compiled %s -> %s" % (po, mo))
