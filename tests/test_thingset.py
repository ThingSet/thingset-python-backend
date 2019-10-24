import thingset

"""
Anatomy of the simple message:
0x1F                    Function ID (publication message)
    -- CBOR starts here:
0xA5
    0x01                        Data Object ID (timestamp)
    0x1A 0x5BC063D8             CBOR data (int32): 1539335128
    0x07                        Data Object ID (eInputTotal_Wh)
    0xFA 0x42f60000             CBOR data (float32): 123.0
    0x08                        Data Object ID (eOutputTotal_Wh)
    0xFA 0x41733333             CBOR data (float32): 15.2
    0x09                        Data Object ID (SOC)
    0x18 0x52                   CBOR data (int32): 82
    0x184E                      Data Object ID (eOutputDay_Wh)
    0x19 0x0356                 CBOR data (int32): 854
"""
THINGSET_SIMPLE_MESSAGE = bytes.fromhex(
    "1F"  # ThingSet first byte
    "A5"  # CBOR's "5 items hash" marker
    "01"
    "1A 5BC063D8"
    "07"
    "FA 42f60000"
    "08"
    "FA 41733333"
    "09"
    "18 52"
    "18 4E"
    "19 0356"
)

THINGSET_TEST_MSG_PAYLOAD_RAW = {
    0x01: 1539335128,
    0x07: 123.0,
    0x08: 15.2,
    0x09: 82,
    0x4E: 854,
}
THINGSET_TEST_DOMAIN_MAPPING = {
    0x01: "timestamp",
    0x07: "eInputTotal_Wh",
    0x08: "eOutputTotal_Wh",
    0x09: "SOC",
    0x4E: "eOutputDay_Wh",
}
THINGSET_TEST_MSG_PAYLOAD_WITH_DOMAIN = {
    "timestamp": 1539335128,
    "eInputTotal_Wh": 123.0,
    "eOutputTotal_Wh": 15.2,
    "SOC": 82,
    "eOutputDay_Wh": 854,
}


def test_version():
    assert thingset.__version__ == '0.1.0'


def test_decode_simple_message_raw():
    decoded_msg = thingset.decode_thingset_message(
        THINGSET_SIMPLE_MESSAGE, floats_precision=3
    )

    assert isinstance(decoded_msg, thingset.Message)

    assert decoded_msg.function == thingset.ThingsetFunction.PUBLICATION_MESSAGE

    assert decoded_msg.payload == THINGSET_TEST_MSG_PAYLOAD_RAW


def test_decode_simple_message_with_domain_dict():
    decoded_msg = thingset.decode_thingset_message_with_domain(
        THINGSET_SIMPLE_MESSAGE, THINGSET_TEST_DOMAIN_MAPPING, floats_precision=3
    )

    assert isinstance(decoded_msg, thingset.MessageWithDomain)

    assert decoded_msg.function == thingset.ThingsetFunction.PUBLICATION_MESSAGE

    assert decoded_msg.payload == THINGSET_TEST_MSG_PAYLOAD_WITH_DOMAIN


def test_decode_simple_message_with_domain_dict_without_all_key_in_the_msg():
    domain_mapping = {**THINGSET_TEST_DOMAIN_MAPPING, **{0x3C: "extraField"}}
    decoded_msg = thingset.decode_thingset_message_with_domain(
        THINGSET_SIMPLE_MESSAGE, domain_mapping, floats_precision=3
    )

    assert isinstance(decoded_msg, thingset.MessageWithDomain)

    assert decoded_msg.function == thingset.ThingsetFunction.PUBLICATION_MESSAGE

    assert decoded_msg.payload == THINGSET_TEST_MSG_PAYLOAD_WITH_DOMAIN


def test_decode_simple_message_with_domain_dict_with_unkwnown_keys_in_the_msg():
    domain_mapping = THINGSET_TEST_DOMAIN_MAPPING.copy()
    del domain_mapping[0x08]

    decoded_msg = thingset.decode_thingset_message_with_domain(
        THINGSET_SIMPLE_MESSAGE, domain_mapping, floats_precision=3
    )

    assert isinstance(decoded_msg, thingset.MessageWithDomain)

    assert decoded_msg.function == thingset.ThingsetFunction.PUBLICATION_MESSAGE

    expected_msg_payload = THINGSET_TEST_MSG_PAYLOAD_WITH_DOMAIN.copy()
    del expected_msg_payload["eOutputTotal_Wh"]
    assert decoded_msg.payload == expected_msg_payload


def test_encode_simple_message_raw():
    raw_msg_payload = THINGSET_TEST_MSG_PAYLOAD_RAW
    msg_function = thingset.ThingsetFunction.PUBLICATION_MESSAGE
    msg = thingset.Message(msg_function, raw_msg_payload)

    thingset_msg = thingset.encode_thingset_message(msg)

    assert isinstance(thingset_msg, bytes)

    assert thingset_msg[0] == thingset.ThingsetFunction.PUBLICATION_MESSAGE.value

    thingset_msg_hex = thingset_msg.hex()
    assert thingset_msg_hex == THINGSET_SIMPLE_MESSAGE.hex()


def test_encode_simple_message_raw_should_give_same_result_than_nodes_c_implementation():
    THINGSET_SIMPLE_MESSAGE_FROM_NODE_C_IMPLEMENTATION = (
        "1fa5011a5bc063d807fa42f6000008fa41733333091852184e190356"
    )
    assert (
        THINGSET_SIMPLE_MESSAGE.hex()
        == THINGSET_SIMPLE_MESSAGE_FROM_NODE_C_IMPLEMENTATION
    )

    raw_msg_payload = THINGSET_TEST_MSG_PAYLOAD_RAW
    msg_function = thingset.ThingsetFunction.PUBLICATION_MESSAGE
    msg = thingset.Message(msg_function, raw_msg_payload)

    thingset_msg = thingset.encode_thingset_message(msg)

    assert isinstance(thingset_msg, bytes)

    assert thingset_msg[0] == thingset.ThingsetFunction.PUBLICATION_MESSAGE.value

    thingset_msg_hex = thingset_msg.hex()
    assert thingset_msg_hex == THINGSET_SIMPLE_MESSAGE_FROM_NODE_C_IMPLEMENTATION


def test_encode_simple_message_raw_with_domain_dict():
    msg_function = thingset.ThingsetFunction.PUBLICATION_MESSAGE
    msg = thingset.MessageWithDomain(
        msg_function, THINGSET_TEST_MSG_PAYLOAD_WITH_DOMAIN
    )

    thingset_msg = thingset.encode_thingset_message_with_domain(
        msg, THINGSET_TEST_DOMAIN_MAPPING
    )

    assert isinstance(thingset_msg, bytes)

    assert thingset_msg[0] == thingset.ThingsetFunction.PUBLICATION_MESSAGE.value

    assert thingset_msg.hex() == THINGSET_SIMPLE_MESSAGE.hex()
