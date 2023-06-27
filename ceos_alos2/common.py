from construct import Int8ub, Int32ub, Struct

record_preamble = Struct(
    "record_sequence_number" / Int32ub,
    "first_record_subtype" / Int8ub,
    "record_type" / Int8ub,
    "second_record_subtype" / Int8ub,
    "third_record_subtype" / Int8ub,
    "record_length" / Int32ub,
)
