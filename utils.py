"""Utility functions found scattered around classes"""

from string import letters, digits

def _normalize(text):
    """lowers and removes all non-ascii characters"""
    text = text.lower()
    text.replace(' ', '')
    text = [c for c in text if c in letters+digits]
    return ''.join(text)
