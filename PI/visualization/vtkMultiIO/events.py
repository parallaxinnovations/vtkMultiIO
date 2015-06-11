import cStringIO
from PI.visualization.common.events import BaseEvent


class HeaderValueModifiedEvent(BaseEvent):

    """
    Event fired whenever an image header value is modified
    """

    def __init__(self, key=None, value=None):

        self._key = key
        self._value = value

    def __str__(self):

        return 'HeaderValue: %s = %s' % (str(self._key), str(self._value))


class HeaderModifiedEvent(BaseEvent):

    """
    Event fired whenever an image header is modified - e.g. for bulk modification
    """

    def __init__(self, hdr):

        self._hdr = hdr

    def __str__(self):

        s = cStringIO.StringIO()

        s.write('Header Key/Value Pairs:\n')

        for key in self._hdr:
            s.write('\t%s = %s\n' % (key, self._hdr[key]))

        return s.getvalue()


class ImageWriteBeginEvent(BaseEvent):

    """
    Event fired whenever an image is about to be written
    """

    def __init__(self, image_index):
        self._image_index = image_index

    def GetImageIndex(self):
        return self._image_index
