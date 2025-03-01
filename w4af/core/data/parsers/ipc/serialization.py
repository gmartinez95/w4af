"""
serialization.py

Copyright 2018 Andres Riancho

This file is part of w4af, https://w4af.net/ .

w4af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w4af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w4af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import os
import pickle
import tempfile

import msgpack


from w4af.core.data.parsers.doc.sgml import Tag
from w4af.core.controllers.misc.temp_dir import create_temp_dir


def write_http_response_to_temp_file(http_response):
    """
    Write an HTTPResponse instance to a temp file using msgpack

    :param http_response: The HTTP response
    :return: The name of the file
    """
    temp = get_temp_file('http')
    data = http_response.to_dict()
    msgpack.dump(data, temp, use_bin_type=True)
    temp.close()
    return temp.name


def load_http_response_from_temp_file(filename, remove=True):
    """
    :param filename: The filename that holds the HTTP response as msgpack
    :param remove: Remove the file after reading
    :return: An HTTP response instance
    """
    # Importing here to prevent import cycle
    from w4af.core.data.url.HTTPResponse import HTTPResponse

    try:
        with open(filename, 'rb') as f:
            data = msgpack.load(f, raw=False)
            result = HTTPResponse.from_dict(data)
    except:
        if remove:
            remove_file_if_exists(filename)
        raise
    else:
        if remove:
            remove_file_if_exists(filename)
        return result


def write_tags_to_temp_file(tag_list):
    """
    Write an Tag list to a temp file using msgpack

    :param tag_list: The Tag list
    :return: The name of the file
    """
    temp = get_temp_file('tags')
    data = [t.to_dict() for t in tag_list]
    msgpack.dump(data, temp, use_bin_type=True)
    temp.close()
    return temp.name


def load_tags_from_temp_file(filename, remove=True):
    """
    :param filename: The filename that holds the Tags as msgpack
    :param remove: Remove the file after reading
    :return: A list containing tags
    """
    try:
        with open(filename, "rb") as f:
            data = msgpack.load(f, raw=False)
        result = [Tag.from_dict(t) for t in data]
    except:
        if remove:
            remove_file_if_exists(filename)
        raise
    else:
        if remove:
            remove_file_if_exists(filename)
        return result


def get_temp_file(_type):
    """
    :return: A named temporary file which will not be removed on close
    """
    directory = create_temp_dir()
    temp = tempfile.NamedTemporaryFile(prefix='w4af-%s-' % _type,
                                       suffix='.pebble',
                                       delete=False,
                                       dir=directory)
    return temp


def write_object_to_temp_file(obj):
    """
    Write an object to a temp file using cPickle to serialize

    :param obj: The object
    :return: The name of the file
    """
    temp = get_temp_file('parser')
    pickle.dump(obj, temp, pickle.HIGHEST_PROTOCOL)
    temp.close()
    return temp.name


def load_object_from_temp_file(filename, remove=True):
    """
    Load an object from a temp file

    :param filename: The filename where the cPickle serialized object lives
    :param remove: Remove the file after reading
    :return: The object instance
    """
    try:
        with open(filename, 'rb') as f:
            result = pickle.load(f)
    except:
        if remove:
            remove_file_if_exists(filename)
        raise
    else:
        if remove:
            remove_file_if_exists(filename)
        return result


def remove_file_if_exists(filename):
    """
    Remove the file if it exists

    :param filename: The file to remove
    :return: None
    """
    try:
        os.remove(filename)
    except:
        pass
