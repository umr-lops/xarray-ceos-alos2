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
