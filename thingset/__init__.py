# @link https://thingset.github.io/spec/functions

# This module is designed to be very generic, so the "Data Object IDs" are supposed to be hard-coded on a higher layer.
# This is why the message payload is just a dict where keys are integers (raw Data Object IDs) rather than strings.
#
# It's up to the upper layer to hard-code that "0x07" means "eInputTotal_Wh" for example -
# the `parse_message_with_domain` can help achieving this.

# N.B.:
#  * We have to introduce a "floats_precision" optional param to our message parsing functions, in order to
#    avoid the classic float issues: that way can round "15.2" to a precision of 3 digits for example, so that we don't
#    end up with a Python representation "15.199999809265137" of that number.
#  * We also have to manually build the CBOR map, as the C implementation of the Nodes firmware forces floats to all
#    be encoded following the "float32" format (which is not the case of our Python implementation).
#
from io import BytesIO
import enum
import typing as t

import cbor2

__version__ = "0.1.0"


MessagePayload = t.Dict[int, t.Any]
MessagePayloadWithDomain = t.Dict[str, t.Any]
PayloadDomainMapping = t.Dict[int, str]


class ThingsetFunction(enum.Enum):
    # @link https://thingset.github.io/spec/functions#request-functions
    READ = 0x01
    WRITE = 0x02
    LIST = 0x03
    GET_DATA_OBJECT_NAME = 0x04
    PUBLICATION_REQUEST = 0x05
    AUTHENTICATION = 0x06
    PRELIMINARY = 0x07
    PUBLICATION_MESSAGE = 0x1F


class Message(t.NamedTuple):
    function: ThingsetFunction
    payload: MessagePayload


class MessageWithDomain(t.NamedTuple):
    function: ThingsetFunction
    payload: MessagePayloadWithDomain


class ParsingError(Exception):
    pass


def decode_thingset_message(msg: bytes, *, floats_precision: int = None) -> Message:
    function = _parse_thingset_msg_function(msg)
    payload = _parse_thingset_msg_payload(msg, floats_precision)

    return Message(function=function, payload=payload)


def decode_thingset_message_with_domain(
    msg: bytes,
    payload_key_mapping: PayloadDomainMapping,
    *,
    floats_precision: int = None,
) -> MessageWithDomain:
    """
    The "payload_key_mapping" must be a dict where keys are the raw binary values of the ThingSet fields we expect to
    to receive, and the values are "domain" translations of these fields.
    So instead of having those raw binary consts as keys of the Message payload you get proper "domain" keys.
    Example:
    ```
        domain_mapping = {
            0x01: "timestamp",
            0x07: "eInputTotal_Wh",
            0x08: "eOutputTotal_Wh",
            0x4A: "tempInt",
        }
        parsed_msg = thingset.parse_message_with_domain(binary_msg, domain_mapping)
        assert parsed_msg.payload == {
            "timestamp": 1552910035,
            "eInputTotal_Wh": 123.0,
            "eOutputTotal_Wh": 15.2,
            "tempInt": 22.3,
        }
    ```
    """
    function = _parse_thingset_msg_function(msg)
    raw_payload = _parse_thingset_msg_payload(msg, floats_precision)

    domain_payload: MessagePayloadWithDomain = {
        domain_key: raw_payload[raw_key]
        for raw_key, domain_key in payload_key_mapping.items()
        if raw_key in raw_payload
    }

    return MessageWithDomain(function=function, payload=domain_payload)


def encode_thingset_message(msg: Message) -> bytes:
    from cbor2.encoder import encode_length

    result = BytesIO()

    # ThingSet first byte:
    result.write(msg.function.value.to_bytes(1, byteorder="little"))
    # CBOR map marker:
    result.write(encode_length(0xA0, len(msg.payload)))

    encoder = cbor2.encoder.CBOREncoder(result)
    for key, value in msg.payload.items():
        encoder.encode(key)
        if isinstance(value, float):
            _encode_float_using_float32(result, value)
        else:
            encoder.encode(value)

    return result.getvalue()


def encode_thingset_message_with_domain(
    msg: MessageWithDomain, payload_key_mapping: PayloadDomainMapping
) -> bytes:
    # We just create a "raw_payload" (where keys are short integers rather than domain strings) by
    # mapping the Domain-ish dct we get to a raw one, and then we call `encode_thingset_message()`.
    flipped_domain_mapping: t.Dict[str, int] = {
        value: key for key, value in payload_key_mapping.items()
    }
    payload_raw = {
        flipped_domain_mapping[key]: value for key, value in msg.payload.items()
    }
    msg_raw = Message(msg.function, payload_raw)

    return encode_thingset_message(msg_raw)


def _parse_thingset_msg_function(msg: bytes) -> ThingsetFunction:
    function_byte = msg[0]
    for protocol_function in ThingsetFunction:
        if protocol_function.value == function_byte:
            return protocol_function
    raise ParsingError(f"Thingset function '{function_byte}' is not implemented")


def _parse_thingset_msg_payload(
    msg: bytes, floats_precision: int = None
) -> MessagePayload:

    # (we ditch the ThingSet byte before decoding the msg with CBOR)
    cbor_msg = msg[1:]
    raw_payload: dict = cbor2.loads(cbor_msg)

    if not isinstance(raw_payload, dict):
        raise ParsingError(
            f"ThingSet payload should be a dict, got {type(raw_payload)} instead"
        )

    payload = {}
    for data_object_id, value in raw_payload.items():
        if floats_precision is not None and isinstance(value, float):
            value = round(value, floats_precision)

        payload[data_object_id] = value

    return payload


def _encode_float_using_float32(target: BytesIO, value: float) -> None:
    # The messages produced by the C code of the nodes always use CBOR_FLOAT32, but the Python
    # implementation of the CBOR we use actually tries to be too smart for us:
    #  * It can either always use CBOR_FLOAT64, for any value of the floats
    #  * Or it can try to optimise things (if the "canonical=True" option is passed to the decoder), and in that case
    #    it will produce CBOR_FLOAT16 for all small floats.
    #    Which is good, because it's shorter to encode.
    #    But in that case we don't produce the same ThingSet messages than the C implementation, which could cause bugs
    #    and/or confusion (as they won't produce the same results).
    #
    # So the safer way to proceed is to copy those 3 lines of code from the "cbor2" package, which are responsible
    # for encoding in CBOR_FLOAT32, and force that encoding on our Python side as well.
    import struct

    encoded = struct.pack(">Bf", 0xFA, value)
    target.write(encoded)
