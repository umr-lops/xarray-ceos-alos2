import datetime

from construct import Adapter
from construct import PaddedString as PaddedString_
from construct import Struct


class AsciiInteger(Adapter):
    def __init__(self, n_bytes):
        base = PaddedString_(n_bytes, "ascii")
        super().__init__(base)

    def _decode(self, obj, context, path):
        stripped = obj.strip()
        if not stripped:
            return -1
        return int(stripped)

    def _encode(self, obj, context, path):
        raise NotImplementedError


class AsciiFloat(Adapter):
    def __init__(self, n_bytes):
        base = PaddedString_(n_bytes, "ascii")
        super().__init__(base)

    def _decode(self, obj, context, path):
        stripped = obj.strip()
        if not stripped:
            stripped = "nan"

        return float(stripped)

    def _encode(self, obj, context, path):
        raise NotImplementedError


class AsciiComplex(Adapter):
    def __init__(self, n_bytes):
        base = Struct(
            "real" / AsciiFloat(n_bytes // 2),
            "imaginary" / AsciiFloat(n_bytes // 2),
        )
        super().__init__(base)

    def _decode(self, obj, context, path):
        return obj.real + 1j * obj.imaginary

    def _encode(self, obj, context, path):
        raise NotImplementedError


class PaddedString(Adapter):
    def __init__(self, n_bytes):
        base = PaddedString_(n_bytes, "ascii")
        super().__init__(base)

    def _decode(self, obj, context, path):
        return obj.strip()

    def _encode(self, obj, context, path):
        raise NotImplementedError


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


class StripNullBytes(Adapter):
    def _decode(self, obj, context, path):
        return obj.strip(b"\x00")

    def _encode(self, obj, context, path):
        raise NotImplementedError


class DatetimeYdms(Adapter):
    def _decode(self, obj, context, path):
        base = datetime.datetime(obj["year"], 1, 1)
        timedelta = datetime.timedelta(
            days=obj["day_of_year"] - 1, milliseconds=obj["milliseconds"]
        )

        return base + timedelta

    def _encode(self, obj, context, path):
        raise NotImplementedError


class DatetimeYdus(Adapter):
    def __init__(self, base, reference_date):
        self.reference_date = reference_date

        super().__init__(base)

    def _decode(self, obj, context, path):
        reference_date = (
            self.reference_date(context) if callable(self.reference_date) else self.reference_date
        )
        truncated = datetime.datetime.combine(reference_date.date(), datetime.time.min)
        return truncated + datetime.timedelta(microseconds=obj)

    def _encode(self, obj, context, path):
        raise NotImplementedError
