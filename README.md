# ThingSet - Python 3.6+ implementation

Python encoder / decoder library for ThingSet protocol

## Example usage

```python
import thingset

# Such a mapping is not mandatory, but working with
# that kind of mapping is often handier than working with 
# the raw binary values when encoding/decoding messages:
MY_IOT_DOMAIN_MAPPING = {
    0x01: "timestamp",
    0x07: "eInputTotal_Wh",
    0x08: "eOutputTotal_Wh",
    0x09: "SOC",
    0x4E: "eOutputDay_Wh",
}

#### Encoding:

my_message_payload = {
    "timestamp": 1539335128,
    "eInputTotal_Wh": 123.0,
    "eOutputTotal_Wh": 15.2,
    "SOC": 82,
    "eOutputDay_Wh": 854,
}

# A ThingSet message always comes with a function - PUBLICATION_MESSAGE here
msg_function = thingset.ThingsetFunction.PUBLICATION_MESSAGE
msg = thingset.MessageWithDomain(msg_function, my_message_payload)

# Encode a message in ThingSet format:
thingset_msg = thingset.encode_thingset_message_with_domain(msg)
assert isinstance(thingset_msg, bytes)

#### Decoding:

# Decoding works pretty much the same:
# Let's say we have a "binary_msg_received_from_mqtt", which type is "bytes":
decoded_msg = thingset.decode_thingset_message_with_domain(
  binary_msg_received_from_mqtt, MY_IOT_DOMAIN_MAPPING, floats_precision=3
)

assert isinstance(decoded_msg, thingset.MessageWithDomain)
assert decoded_msg.function == thingset.ThingsetFunction.PUBLICATION_MESSAGE
assert decoded_msg.payload == my_message_payload
```

## Quick overview of the public API of the "thingset" module

```python
import enum
import typing as t


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
    ...


def decode_thingset_message_with_domain(
    msg: bytes,
    payload_key_mapping: PayloadDomainMapping,
    *,
    floats_precision: int = None,
) -> MessageWithDomain:
    ...


def encode_thingset_message(msg: Message) -> bytes:
    ...
 

def encode_thingset_message_with_domain(
    msg: MessageWithDomain, payload_key_mapping: PayloadDomainMapping
) -> bytes:
    ...

```

The code source of the library fits in one single file and is pretty small,
so while waiting for a proper documentation you can read it and have a look at 
the tests suite to learn more :-)
