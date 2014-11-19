# encoding: utf-8
import os
import glob
import sys
from email import message_from_file
from email.header import decode_header
import base64
import re
import csv

name_from_dispo_pat = re.compile(r'filename="(.+?)"')
def name_from_dispo(dispo):
    lines = dispo.split('\n')
    for line in lines:
        line = line.strip()
        got = name_from_dispo_pat.search(line)
        if got:
            return got.group(1)
    raise ValueError('No file name found in `%s` (%s)' % (dispo, lines))

charset_pat = re.compile(r'charset="(.+)"')
def choose_content(msg):
    content_pl = msg.get_payload()[0]
    all_pl = content_pl.get_payload()
    if isinstance(all_pl, str):
        # Without alternative: choose the text/plain one
        if content_pl.get('Content-Transfer-Encoding') == 'base64':
            return base64.b64decode(all_pl)
        else:
            return all_pl
    for pl in all_pl:
        # Multipart/alternative: choose the text/plain one
        content_type = pl['Content-Type']
        if content_type.startswith('text/plain'):
            charset = charset_pat.search(content_type).group(1)
            assert pl['Content-Transfer-Encoding'] == 'base64'
            pl = base64.b64decode(pl.get_payload())
            return pl.decode(charset)

def write_attachments(msg, i, to_dir='out/attachments/'):
    filenames = []
    for pl in msg.get_payload():
        dispo = pl.get('Content-Disposition')
        if not dispo:
            continue

        filename = name_from_dispo(dispo)
        enc = pl.get('Content-Transfer-Encoding')
        assert enc == 'base64'
        b64_content = pl.get_payload()
        assert isinstance(b64_content, str)

        real_name = format_sn(i) + '-' + filename
        filenames.append(real_name)
        path = to_dir + real_name
        with open(path, 'wb') as fout:
            content = base64.b64decode(b64_content)
            fout.write(content)
        print('Wrote %d bytes to %s' % (len(content), path))
        i += 1
    return filenames

def format_sn(i):
    return '%06d' % i

headers = 'SN DATE SENDER RECEIVER CC SUBJECT CONTENT ATTACHMENT'.split()
def write_csv_row(writer, msg, i, attach_out_dir):
    sn = format_sn(i)

    names = write_attachments(msg, i, attach_out_dir)

    [(sub_raw, sub_enc)] = decode_header(msg['Subject'])
    if sub_enc is None:
        print(sub_raw)
        sub = sub_raw
    else:
        sub = sub_raw.decode(sub_enc)
    content = choose_content(msg)

    writer.writerow({
        'SN': sn,
        'DATE': msg['Date'],
        'SENDER': msg['From'],
        'RECEIVER': msg['To'],
        'CC': msg['Cc'],
        'SUBJECT': sub,
        'CONTENT': content,
        'ATTACHMENT': ', '.join(names)
    })
    return i + 1 + len(names)

def ensure_dir(d):
    try:
        os.makedirs(d)
    except OSError:
        pass

def dummy_progress(title, percent):
    pass

def run(in_dir, csv_out_dir, attach_out_dir, progress=dummy_progress):
    with open(csv_out_dir + 'sample-output.csv', 'w', newline='',
            encoding='utf-16') as csvf:
        writer = csv.DictWriter(csvf, headers)
        writer.writeheader()

        i = 0
        all_files = glob.glob(in_dir + '*.eml')
        num_files = len(all_files)
        for eml_path in all_files:
            progress(os.path.basename(eml_path), float(i) / num_files)
            with open(eml_path) as f:
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
