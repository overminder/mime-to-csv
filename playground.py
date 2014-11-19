#!/usr/bin/env python3

""" Just copied from
    https://docs.python.org/2/library/email-examples.html
"""

import mimetypes
from email import message_from_file
import sys
import os

def extract_parts(msg, i):
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        filename = part.get_filename()
        if not filename:
            ext = mimetypes.guess_extension(part.get_content_type())
            if not ext:
                if part.get_content_type() == 'text/plain':
                    ext = '.txt'
                else:
                    assert False, part.get_content_type()
            filename = 'part-%03d%s' % (i, ext)
        yield (filename, part.get_payload(decode=True))
        i += 1

with open(sys.argv[1], encoding='ISO8859') as f:
    msg = message_from_file(f)

for name, content in extract_parts(msg, 0):
    with open(os.path.join(sys.argv[2], name), 'wb') as fout:
        fout.write(content)
