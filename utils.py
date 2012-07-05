"""Utility functions."""

import re
import unicodedata

ASCII_APPROX = {
    u'\u00c6': 'Ae',
    u'\u00e6': 'ae',
    u'\u2014': ' -- ',
}

# Replace utf-8 with ascii approximations.
def asciify_utf8(text):
    return ''.join((ASCII_APPROX[s] if s in ASCII_APPROX else s for s in text))

# Clean up a string and convert to ascii.
def asciify_decode(text):
    return asciify_unicode(text.decode('utf-8'))

def asciify_encode(text):
    return asciify_unicode(unicode(text))

def asciify_unicode(text):
    return asciify_utf8(unicodedata.normalize('NFKD', text)).encode(
        'ascii', 'ignore').strip()
