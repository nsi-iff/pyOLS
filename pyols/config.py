# XXX: This is not done yet.  Do it :)

_config = {'db': {'uri': 'sqlite:///tmp/test.sqlite'}}

def _get(path, config=_config):
    (section, subsection) = (path[0], path[1:])
    if subsection:
        return _get(subsection, config[section])
    else:
        return config[section]

def get(*path):
    """ Return config option stored in path.
        For example, given the config:
        [db]
        uri = sqlite:///tmp/123
        >>> config.get('db', 'uri')
        'sqlite:///tmp/123'
        >>> """
    return _get(path)
