#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import re
import pprint
from collections import defaultdict

SAMPLE_FILE = "sample.osm"

street_type_re = re.compile(r'^\S+(\b|\.)', re.IGNORECASE)


# expected types of street , otherwise we will consider it a street
expected_street_type = ["calle", "avenida", "plaza", "paseo",
                        "pasaje", "ronda", "travesia",
                        "costanilla", "callejon", "camino",
                        "carretera", "bulevar", "autovia",
                        "rinconada", "glorieta", "urbanizacion",
                        "senda", "poligono", "finca"]


def audit_street_type(street_types, street_name):
    """ add the street name to the street_type list if
    the street name  is not the list of expected values

    Args:
        street_types (dict) : dictionary of unmatched street names
        street_name (str) : the street name to validate
    """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type.lower() not in expected_street_type:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    """ determines if the element is of the street type

    Args:
        elem (ET.element]) : XML_element
    Returns:
        boolean : true if the element is a street
    """
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile, is_type, audit_type, filter_fun=lambda x: x):
    """ audits an osm xml file for a given type of tag

    Args:
        osmfile (str) : OSM file tag
        is_type (ET.element)=>boolean : determines if the parsed xml element is
                                        of the desired kind
        audit_type (dict,str)=>void : functions that adds the needed values to
                                      the list_types dictionary
        filter_fun (str)=>str : optional filter to be applied to the values
    Returns:
        dict : dictionary of the value passing the audit function.
    """
    osm_file = open(osmfile, "r")
    list_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_type(tag):
                    # check that there is the required value element
                    if "v" not in tag.attrib:
                        print tag
                    value = tag.attrib['v']
                    audit_type(list_types, filter_fun(value))
    osm_file.close()
    return list_types


street_types = audit(SAMPLE_FILE, is_street_name, audit_street_type)

print "\n\nSTREET NAMES\n\n"

pprint.pprint(dict(street_types))

# Filter LEISURES
expected_leisures = ["park", "natural_reserve", "garden"]


def audit_leisure_type(leisure_types, leisure_name):
    """ add the leisure name to the leisure_type list if
    the leisure name  is not the list of expected values

    Args:
        leisure_types ([]]) : List of unmatched leisure names
        leisure_name (str) : the leisure name to validate
    """
    if leisure_name:
        if leisure_name.lower() not in expected_leisures:
            leisure_types[leisure_name].add(leisure_name)


def is_leisure(elem):
    """ determines if the element is of the leisure type

    Args:
        elem (ET.element]) : XML_element
    Returns:
        boolean : true if the element is a leisure
    """
    return (elem.attrib['k'] == "leisure")


leisure_types = audit(SAMPLE_FILE, is_leisure, audit_leisure_type)


print "\n\nLEISURES\n\n"
# show the types of leisures in the sample file
pprint.pprint(dict(leisure_types))


expected_amenities = []


def audit_amenities_type(amenities_types, amenities_name):
    """ add the amenities name to the amenities_type list if
    the amenities name  is not the list of expected values

    Args:
        amenities_types ([]]) : List of unmatched amenities names
        amenities_name (str) : the amenities name to validate
    """
    if amenities_name:
        if amenities_name.lower() not in expected_amenities:
            amenities_types[amenities_name].add(amenities_name)


def is_amenities(elem):
    """ determines if the element is of the amenities type

    Args:
        elem (ET.element]) : XML_element
    Returns:
        boolean : true if the element is a amenities
    """
    return (elem.attrib['k'] == "amenity")


amenities_types = audit(SAMPLE_FILE, is_amenities, audit_amenities_type)

print "\n\nAMENITIES\n\n"
# show the types of leisures
pprint.pprint(sorted(amenities_types.keys()))

CP_RE = re.compile("^(28|45|05|40|19|16)[0-9]{3}$")


def audit_cp_type(postcode_types, postcode_name):
    """ add the postcode name to the postcode_type list if
    the postcode name  is not the list of expected values

    Args:
        postcode_types ([]]) : List of unmatched postcode names
        postcode_name (str) : the postcode name to validate
    """
    if postcode_name:
        if not CP_RE.match(postcode_name):
            postcode_types[postcode_name].add(postcode_name)


def is_cp(elem):
    """ determines if the element is of the postcode type

    Args:
        elem (ET.element]) : XML_element
    Returns:
        boolean : true if the element is a postcode
    """
    return (elem.attrib['k'] == "addr:postcode")


postcode_types = audit(SAMPLE_FILE, is_cp, audit_cp_type)

# show the incorrect postcodes
print "\n\nPOSTCODES\n\n"
pprint.pprint(dict(postcode_types))
