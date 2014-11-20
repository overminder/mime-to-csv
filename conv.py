#!/usr/bin/env python3
# encoding: utf-8

import os
import glob
import sys
from email import message_from_file
from email.header import decode_header
import csv
import chardet
from operator import itemgetter

def extract_parts(msg, i):
    files = []
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        filename = part.get_filename()
        if not filename:
            # Is an email content
            if part.get_content_type() == 'text/plain':
                content_bs = part.get_payload(decode=True)
                charset = part.get_charset()
                if not charset:
                    # In most of the cases it's utf-8. However... Ouck Futlook.
                    guess_result = chardet.detect(content_bs)
                    charset = guess_result['encoding']
                    print('* Content: No charset found. '
                          'Guessed to be %(encoding)s, '
                          'confidence: %(confidence)s' % guess_result)
                else:
                    print('*Content: charset is %s' % charset)
                content = content_bs.decode(charset)
                i += 1
        else:
            files.append(('%06d-%s' % (i, filename),
                part.get_payload(decode=True)))
            i += 1
    return (files, content), i

def format_sn(i):
    return '%06d' % i

def decode_header_to_string(msg, header_name):
    [(raw, enc)] = decode_header(msg[header_name])
    if enc is None:
        return raw
    else:
        return raw.decode(enc)

headers = 'SN DATE SENDER RECEIVER CC SUBJECT CONTENT ATTACHMENT'.split()
def write_csv_row(writer, msg, i, attach_out_dir):
    sn = format_sn(i)
    i += 1

    # Extract content and attachments (from MIME parts)
    (attachments, email_content), new_i = extract_parts(msg, i)

    # Make row
    row = {
        'SN': sn,
        'DATE': decode_header_to_string(msg, 'Date'),
        'SENDER': decode_header_to_string(msg, 'From'),
        'RECEIVER': decode_header_to_string(msg, 'To'),
        'CC': decode_header_to_string(msg, 'Cc'),
        'SUBJECT': decode_header_to_string(msg, 'Subject'),
        'CONTENT': email_content,
        'ATTACHMENT': ', '.join(fn for (fn, _) in attachments)
    }

    print('* Title: `%s`' % row['SUBJECT'])

    # Save attachments to disk
    for (filename, bs) in attachments:
        print('  - With attachment %s (%d bytes)' % (filename, len(bs)))
        with open(os.path.join(attach_out_dir, filename), 'wb') as outf:
            outf.write(bs)
    if not attachments:
        print('  - Without attachments')

    print('')

    writer.writerow(row)
    return new_i

def ensure_dir(d):
    try:
        os.makedirs(d)
    except OSError:
        pass

def dummy_progress(title, percent):
    pass

def run(in_dir, csv_out_dir, attach_out_dir, progress=dummy_progress):
    with open(csv_out_dir + 'sample-output.csv', 'w', newline='',
            encoding='utf-8') as csvf:
        writer = csv.DictWriter(csvf, headers)
        writer.writeheader()

        i = 0
        all_files = glob.glob(in_dir + '*.eml')
        num_files = len(all_files)
        for eml_path in all_files:
            progress(os.path.basename(eml_path), float(i) / num_files)
            with open(eml_path, encoding='ISO8859') as f:
                print('Converting %s' % eml_path)
                msg = message_from_file(f)
                i = write_csv_row(writer, msg, i, attach_out_dir)
    progress(None, 1)

def main():
    prog_name, *args = sys.argv
    if len(args) != 2:
        print('Usage: %s input-dir output-dir' % prog_name)
        sys.exit(-1)
    (in_dir, csv_out_dir) = args

    attach_out_dir = csv_out_dir + 'attachments/'
    ensure_dir(attach_out_dir)
    run(in_dir, csv_out_dir, attach_out_dir)

if __name__ == '__main__':
    main()
