from construct import Adapter, Enum, Int8ub, Int16ub, Int32ub, Int64ub


class Flag(Adapter):
    bases = {
        1: Int8ub,
        2: Int16ub,
        4: Int32ub,
        8: Int64ub,
    }

    def __init__(self, size):
        base = self.bases.get(size)
        if base is None:
            raise ValueError(f"unsupported size: {size}")

        super().__init__(base)

    def _decode(self, obj, context, path):
        return bool(obj)

    def _encode(self, obj, context, path):
        return int(obj)


sar_channel_id = Enum(Int16ub, single_polarization=1, dual_polarization=2, full_polarization=4)
sar_channel_code = Enum(Int16ub, L=0, S=1, C=2, X=3, KU=4, KA=5)
pulse_polarization = Enum(Int16ub, horizontal=0, vertical=1)
chirp_type_designator = Enum(Int16ub, linear_fm_chirp=0, phase_modulators=1)
platform_position_parameters_update = Enum(Int32ub, repeat=0, update=1)
