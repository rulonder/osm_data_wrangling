#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import re
import unicodedata
import codecs
import json
from titlecase import titlecase

# Define input file
OSM_FILE = "madrid_spain.osm"

# expected types of street , otherwise we will consider it a street
expected_street_type = ["calle", "avenida", "plaza", "paseo",
                        "pasaje", "ronda", "travesia",
                        "costanilla", "callejon", "camino",
                        "carretera", "bulevar", "autovia",
                        "rinconada", "glorieta", "urbanizacion",
                        "senda", "poligono", "finca"]


# Filtering of the addreses
mapping_road = {"call": "calle",
                "c/": "calle",
                "ctra.": "carretera",
                "cr": "carretera",
                "calleja/callejon": "callejon",
                "urb.": "urbanizacion",
                "urb": "urbanizacion",
                "Pz": "plaza",
                "Pz.": "plaza",
                "av": "Avenida",
                "avd": "avenida",
                "avd.": "avenida",
                "pasaje/pasadizo": "pasaje",
                "av.": "avenida",
                "rcda.": "rinconada",
                "CARRERA CARRETERA": "carretera",
                "CARRERA VALENC∏IA": "carrera"
                }


def get_update_first_word_filter(mapping):
    """ this function return a function that updates a name
    based on the mappings input only for the first word

    Args:
        mapping (dict) : dictionary where the key is the value to be modified
                         and the value is the new value.

    Returns:
        function: filters strings based on the provided mapping.
    """
    def update_name(name):
        """ this function takes a string and translates/modifies the first word
        based on a dictionary

        Args:
            name (str) : the string to be modified.

        Returns:
            string: The final string where the words have been updated.
        """
        words = name.split()
        if words[0] in mapping:
            words[0] = mapping[words[0]]
        result = " ".join(words)
        return result
    return update_name


def set_default_street(name):
    """ this function enforce the name to have a valid value
    or the default one i.e. "calle"

    Args:
        name (str) : the street adress.

    Returns:
        string: The final string where the street type is enforce
                to be in the expecte street type list.
    """
    words = name.split()
    if words[0] not in expected_street_type:
        name = "calle " + name
    return name


def strip_accents_filter(name):
    """ remove accents in the name
    obtained from stackoverflow
    http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string

    Args:
        name (str) : the street adress.

    Returns:
        string: Tthe street adress without accents.
    """
    name = unicode(name)
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')


def lower_name_filter(name):
    """ lower case the name

    Args:
        name (str) : the street adress.

    Returns:
        string: The street address in lowe case.
    """
    return name.lower()


def remove_leading_CL_filter(name):
    """ remove leading "CL" in the string
    e.g. from "CL carretera uno" to "carretera uno"

    Args:
        name (str) : the street adress.

    Returns:
        string: The street address withouth leading CL.
    """
    if name.startswith("CL "):
        name = name[3:]
    return name


def change_cr_filter(name):
    """ translates leading C.N.

    Args:
        name (str) : the street adress.

    Returns:
        string: The street with C.N. tranlated if any
    """
    if name.startswith("C.N."):
        name = "carretera n-" + name[4:]
    return name


# Spanish road matching regexp
ROAD_RE = re.compile(r'[a-z]+\-[0-9]+', re.IGNORECASE)


def identify_road_filter(name):
    """ Identifies road names in spanish convection adding the carretera type

    Args:
        name (str) : the street adress.

    Returns:
        string: The street with the added carretera type if matched
    """
    if ROAD_RE.match(name):
        name = "carretera " + name
    return name


def title_name_filter(name):
    """ title format the name in order to save it

    Args:
        name (str) : the street adress.

    Returns:
        string: The street address in title case.
    """
    return titlecase(name)


def gen_apply_filters(filters):
    """ Returns a function that applies a series of filters to an string

    Args:
        filters (list(functions)) : list of funtions,these funtions should take
                a string as input and return a string
                (str) => str

    Returns:
        function (str)=>str : filtering funtion based on the list of filters
    """
    def filter_function(value):
        temp = value
        for function in filters:
            temp = function(temp)
        return temp
    return filter_function


# build list of functions that we will apply to clean our street address
FILTER_STREET = gen_apply_filters([remove_leading_CL_filter, change_cr_filter,
                                  lower_name_filter, strip_accents_filter,
                                  get_update_first_word_filter(mapping_road),
                                  set_default_street, title_name_filter])


# Filtering of the amenities
mapping_amen = {"biblioteca": "library",
                "espacio_trabajo": "coworking_space"
                }

# build list of functions that we will apply to clean our street address
FILTER_AMENITY = gen_apply_filters([get_update_first_word_filter(mapping_amen)])


# Filtering of the leisures
mapping_leisures = {"nature_reserve": "natural_reserve"}

# build list of functions that we will apply to clean our street address
FILTER_LEISURES = gen_apply_filters([get_update_first_word_filter(mapping_leisures)])


# regexp matching valid postcodes
CP_RE = re.compile("^[a-zA-Z]?((28|45|05|40|19|16)\d{3})$")


def remove_invalid_postcode(postcode):
    """ Filters the invalid postcodes,
    it also removes leading letters in postcodes
    e.g. "E28765" => "28765"

    Args:
        name (str) : the postcode.

    Returns:
        string|None: The string if it is a valid postcode or None otherwise
    """
    clean_postcode = CP_RE.findall(postcode)
    if clean_postcode:
        return clean_postcode[0]
    else:
        return None


FILTER_POSTCODE = gen_apply_filters([remove_invalid_postcode])


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


CREATED = ["version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    """ Sahpes the xml element in the osm file into a more
    json firendly representation, in order to later update it
    inot a mongodb database

    Args:
        element (ET.element) : the xml element.

    Returns:
        dict|None: returns a dict representing the element
                or None it is not a node or way element
    """
    node = {}
    if element.tag == "node" or element.tag == "way":
        node["type"] = element.tag
        # parse attributes
        for k, v in element.attrib.iteritems():
            if k in CREATED:
                if "created" not in node:
                    node["created"] = {}
                node["created"][k] = v
            elif k == "lat":
                if "pos" not in node:
                    node["pos"] = [0.0, 0.0]
                node["pos"][0] = float(v)
            elif k == "lon":
                if "pos" not in node:
                    node["pos"] = [0.0, 0.0]
                node["pos"][1] = float(v)
            else:
                node[k] = v
        # parse child elements, that are contained in the tag elements with key and value attributes
        for child in element.iter("tag"):
            if "k" in child.attrib:
                if lower.match(child.attrib["k"]):
                    if child.attrib["k"] == "amenity":
                        amenity = FILTER_AMENITY(child.attrib["v"])
                        node["amenity"] = amenity
                    elif child.attrib["k"] == "leisure":
                        leisure = FILTER_LEISURES(child.attrib["v"])
                        node["leisure"] = leisure
                    else:
                        node[child.attrib["k"]] = child.attrib["v"]
                elif lower_colon.match(child.attrib["k"]):
                    first, second = child.attrib["k"].split(":")
                    if first == "addr":
                        if "address" not in node:
                            node["address"] = {}
                        # apply the previously creted data cleaning functions
                        if second == "street":
                            node["address"][second] = FILTER_STREET(child.attrib["v"])
                        elif second == "postcode":
                            postcode = FILTER_POSTCODE(child.attrib["v"])
                            if postcode:
                                node["address"][second] = postcode
                        else:
                            node["address"][second] = (child.attrib["v"])
                    else:
                        first = first + ":"
                        if first not in node:
                            node[first] = {}
                        node[first][second] = child.attrib["v"]
                elif problemchars.search(child.attrib["k"]):
                    pass
                else:
                    pass
        for child in element.iter("nd"):
            if "ref" in child.attrib:
                if "node_refs" not in node:
                    node["node_refs"] = []
                node["node_refs"].append((child.attrib["ref"]))
        element.clear()
        return node
    else:
        return None


def process_map(file_in, pretty=False):
    """ generates a json file from an xml osm file

    Args:
        file_in (str) : The osm xml file path.
        pretty (boolean) : Pretty format the output json for legibility
    """
    file_out = "{0}.json".format(file_in)
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in, events=["end"]):
            el = shape_element(element)
            if el:
                if pretty:
                    fo.write(json.dumps(el, indent=2) + "\n")
                else:
                    fo.write(json.dumps(el) + "\n")
            # element.clear()


process_map(OSM_FILE, False)
