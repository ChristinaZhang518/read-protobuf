"""
read-protobuf

Attributes:
    DEFAULTS (dict): Default inputs
"""

import pandas as pd

DEFAULTS = {
    'flatten': True,
    'prefix_nested': False
}


class ProtobufReader(object):
    """ ProtobufReader class to handle interpretation"""

    def __init__(self, flatten=DEFAULTS['flatten'],
                       prefix_nested=DEFAULTS['prefix_nested']):

        self.flatten = flatten
        self.prefix_nested = prefix_nested

    def to_array(self, Message, field=None):
        """Convert an arbitrary message to an array

        Args:
            Message (TYPE): Description
            field (string, optional): field within message to convert to array

        Returns:
            TYPE: Description
        """
        if field:
            array = [self.interpret_message(m) for m in getattr(Message, field)]
        else:
            array = [self.interpret_message(Message)]

        return array

    def interpret_message(self, Message):
        """Interpret a message into a dict or array

        Args:
            Message (TYPE): Description

        Returns:
            dict | list: protobuf message interpreted into a list or dict
        """

        data = {}  # default to dict
        for field in Message.ListFields():

            # repeated nested message
            if field[0].type == field[0].TYPE_MESSAGE and field[0].label == field[0].LABEL_REPEATED:

                # is this the only field in the pb? if so, look at flatten
                if len(Message.ListFields()) == 1 and self.flatten:
                    data = self.to_array(Message, field[0].name)

                # if there are multiple repeated messages in object, set as keys
                else:
                    data[field[0].name] = self.to_array(Message, field[0].name)

            # nested message
            elif field[0].type == field[0].TYPE_MESSAGE:
                if self.flatten:
                    nested_dict = self.interpret_message(field[1])
                    for key in nested_dict:
                        if key in data or self.prefix_nested:
                            data['{}.{}'.format(field[0].name, key)] = nested_dict[key]
                        else:
                            data[key] = nested_dict[key]
                else:
                    data[field[0].name] = self.interpret_message(field[1])

            # repeated scalar
            elif field[0].label == field[0].LABEL_REPEATED:
                data[field[0].name] = list(field[1])

            # scalar
            else:
                data[field[0].name] = field[1]

        return data


def read_protobuf(pb, MessageType, flatten=DEFAULTS['flatten'],
                               prefix_nested=DEFAULTS['prefix_nested']):
    """Summary

    Args:
        pb (string | bytes): file path to pb file or bytes from pb file
        MessageType (google.protobuf.message.Message): Message class of pb message
        flatten (bool, optional): flatten all nested objects into a 2-d dataframe. This will also collapse  repeated message containers
        prefix_nested (bool, optional): prefix all flattened objects with parent keys

    Returns:
        DataFrame: pandas dataframe with interpreted pb data
    """

    # message parsing
    if isinstance(pb, str):
        with open(pb, 'rb') as f:
            Message = MessageType.FromString(f.read())

    elif isinstance(pb, bytes):
        Message = MessageType.FromString(pb)
    else:
        raise TypeError('unknown input source for protobuf')

    # instantiate reader
    reader = ProtobufReader(flatten, prefix_nested)

    # intepret message
    data = reader.interpret_message(Message)

    # put data into frame
    df = pd.DataFrame(data)

    return df