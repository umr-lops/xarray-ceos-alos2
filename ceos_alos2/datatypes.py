from construct import Adapter
from construct import PaddedString as PaddedString_


class AsciiIntegerAdapter(Adapter):
    def _decode(self, obj, context, path):
        return int(obj.rstrip())

    def _encode(self, obj, context, path):
        raise NotImplementedError


class AsciiFloatAdapter(Adapter):
    def _decode(self, obj, context, path):
        stripped = obj.rstrip()
        if not stripped:
            stripped = "nan"

        return float(stripped)

    def _encode(self, obj, context, path):
        raise NotImplementedError


class PaddedStringAdapter(Adapter):
    def _decode(self, obj, context, path):
        return obj.strip()

    def _encode(self, obj, context, path):
        raise NotImplementedError


def AsciiInteger(n_bytes):
    return AsciiIntegerAdapter(PaddedString_(n_bytes, "ascii"))


def AsciiFloat(n_bytes):
    return AsciiFloatAdapter(PaddedString_(n_bytes, "ascii"))


def PaddedString(n_bytes):
    return PaddedStringAdapter(PaddedString_(n_bytes, "ascii"))


class Factor(Adapter):
    def __init__(self, obj, factor):
        super().__init__(obj)
        self.factor = factor

    def _decode(self, obj, context, path):
        return obj * self.factor

    def _encode(self, obj, context, path):
        raise NotImplementedError


class Metadata(Adapter):
    def __init__(self, obj, **kwargs):
        super().__init__(obj)

        self.attrs = kwargs

    def _decode(self, obj, context, path):
        return (obj, self.attrs)

    def _encode(self, obj, context, path):
        raise NotImplementedError
