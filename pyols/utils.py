"""Utility functions found scattered around classes"""

from string   import letters, digits
from DateTime import DateTime
from random   import random


def _normalize(text):
    """lowers and removes all non-ascii characters"""
    text = text.lower()
    text.replace(' ', '')
    text = [c for c in text if c in letters+digits]
    return ''.join(text)

def generateUniqueId(type_name):
    """Tries to generate an unique object id from 'type', timestamp and randomness.

    Stolen from CMFPlone/plone_scripts/generateUniqueId.py
    """
    now=DateTime()
    time='%s.%s' % (now.strftime('%Y-%m-%d'), str(now.millis())[7:])
    rand=str(random())[2:6]
    prefix=''
    suffix=''

    if type_name is not None:
        prefix = type_name.replace(' ', '_')+'.'
    prefix=prefix.lower()

    return prefix+time+rand+suffix