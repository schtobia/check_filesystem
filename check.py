#! /usr/bin/python
# -*- coding: utf-8 -*-
import hashlib
import json
import os
import logging
import logging.handlers
import sys
import traceback

#enable syslog logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
handler = logging.handlers.SysLogHandler(address = '/dev/log')
handler.setFormatter(logging.Formatter('%(module)s: %(levelname)s: %(message)s'))
log.addHandler(handler)

# write all uncaught exceptions to syslog
sys.excepthook = lambda ex_cls, ex, tb: log.critical('{0}: {1} -- {2}'.format(ex_cls, ex, traceback.format_tb(tb)))

def calculate_sha256_from_file(file_name, size = 0):
    block_size = 4096
    calculated_hash = hashlib.sha256()
    with open(file_name) as target_file:
        if size == 0:
            for chunk in iter(lambda: target_file.read(block_size), b""):
                calculated_hash.update(chunk)
        else:
            while size > block_size:
                calculated_hash.update(target_file.read(block_size))
                size -= block_size
            calculated_hash.update(target_file.read(size))
    return calculated_hash.hexdigest()

def calc_sha256_on_luksHeader(device_name):
    if not os.path.exists(device_name):
        raise RuntimeError("device " + device_name + " not present!")
    temp_backup_name = os.tmpnam()
    header_sum_actual = None
    if os.system("cryptsetup luksHeaderBackup --header-backup-file=" + temp_backup_name + " " + device_name) == 0:
        header_sum_actual = calculate_sha256_from_file(temp_backup_name)
    try:
        os.remove(temp_backup_name)
    except OSError:
        pass
    return header_sum_actual

if __name__ == '__main__':
    key_file_name = None
    try:
        key_file_name = sys.argv[1]
    except IndexError:
        print "Usage: " + sys.argv[0] + " <key file json>"
        exit(1)

    json_data = None
    with open(key_file_name, 'r') as text_file:
        json_data = json.load(text_file)

    exitCode = 0
    data_has_changed = False
    for device_name, device in json_data.iteritems():
        if device.has_key('luksHeader'):
            desired_sum = device['luksHeader']
            actual_sum = calc_sha256_on_luksHeader(device_name)
            if desired_sum == None:
                device['luksHeader'] = actual_sum
                log.notice(u"○ Updating configuration file: LUKS header for " + device_name + ": " + actual_sum[:8] + u"…")
                data_has_changed = True
            elif desired_sum <> actual_sum:
                log.error(u"✗ LUKS header for " + device_name + " failed: Should be " + desired_sum[:8] + u"…" + ", but really is " + actual_sum[:8] + u"…")
                exitCode = 1
            else:
                log.info(u"✓ LUKS header for " + device_name + " correct: " + actual_sum[:8] + u"…")
        if device.has_key("sha256"):
            desired_sum = device['sha256']
            if device.has_key('size'):
                size = device['size']
            else:
                size = 0
            actual_sum = calculate_sha256_from_file(device_name, size)
            if desired_sum == None:
                device['sha256'] = actual_sum
                log.notice(u"○ Updating configuration file: SHA sum for " + device_name + ": " + actual_sum[:8] + u"…")
                data_has_changed = True
            elif desired_sum <> actual_sum:
                log.error(u"✗ SHA sum for " + device_name + " failed: Should be " + desired_sum[:8] + u"…" + ", but really is " + actual_sum[:8] + u"…")
                exitCode = 1
            else:
                log.info(u"✓ SHA sum for " + device_name + " correct: " + actual_sum[:8] + u"…")

    if data_has_changed:
        log.notice("Checksums have changed, updating key file")
        with open(key_file_name, 'w') as text_file:
            json.dump(json_data, text_file)

    exit(exitCode)
