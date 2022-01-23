from zope import event

from PI.visualization.vtkMultiIO.events import HeaderValueModifiedEvent, HeaderModifiedEvent


class HeaderDictionary(dict):

    """
    HeaderDictionary - a Zope event aware Python dictionary.

    HeaderDictionary acts just like a basic dictionary, but will generate a zope
    event whenever values are modified within the dictionary.
    """

    def __init__(self, _dict={}):

        for key in _dict:
            dict.__setitem__(self, key, _dict[key])

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        event.notify(HeaderValueModifiedEvent(key, value))

    def invokeModifiedEvent(self):
        event.notify(HeaderModifiedEvent(self))
