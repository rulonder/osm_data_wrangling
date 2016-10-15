#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import re
import pprint
import unicodedata
import codecs
import json
from collections import defaultdict

# Define input file
OSM_FILE = "madrid_spain.osm"

# expected types of street , otherwise we will consider it a street
expected_street_type = ["calle","avenida","plaza","paseo","pasaje","ronda","travesia",
            "costanilla","callejon","camino","carretera","bulevar","autovia",
            "rinconada", "glorieta","urbanizacion","senda","poligono","finca"]


# Filtering of the addreses
mapping = { "call": "calle",
            "c/": "calle",
            "ctra.":"carretera",
            "cr":"carretera",
            "calleja/callejon":"callejon",
            "urb.":"urbanizacion",
            "urb":"urbanizacion",
            "Pz":"plaza",
            "Pz.":"plaza",
            "av": "Avenida",
            "avd": "avenida",
            "avd.": "avenida",
            "pasaje/pasadizo":"pasaje",
            "av.": "avenida",
            "rcda.":"rinconada",
            "CARRERA CARRETERA":"carretera",
            "CARRERA VALENCIA":"carrera"
            }
# this function return a function that updates a name based on the mappings input only for the first word
def get_update_first_word_filter(mapping):
    def update_name(name):
        words = name.split()
        if words[0] in mapping:
            words[0] = mapping[words[0]]
        name = " ".join(words)
        return name
    return update_name

def set_default_street(name):
    words = name.split()
    if words[0] not in expected_street_type:
        name = "calle "+ name
    return name

# remove accent function, obtained from stackoverflow http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents_filter(name):
   name = unicode(name)
   return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

def lower_name_filter(name):
    return name.lower()

def remove_leading_CL_filter(name):
    if name.startswith("CL "):
        name = name[3:]
    return name

def change_cr_filter(name):
    if name.startswith("C.N."):
        name = "carretera n-"+name[4:]
    return name


ROAD_RE = re.compile(r'[a-z]+\-[0-9]+', re.IGNORECASE)

def identify_road_filter(name):
    if ROAD_RE.match(name):
        name = "carretera "+name
    return name
    
# this function applies a series of transformations or filters to an initial value
def gen_apply_filters(filters):
    def filter_function(value):
        temp = value
        for function in filters:
            temp = function(temp)
        return temp
    return filter_function


# build list of functions that we will apply to clean our street address
FILTER_STREET = gen_apply_filters([remove_leading_CL_filter,change_cr_filter, 
                                  lower_name_filter, strip_accents_filter,
                                  get_update_first_word_filter(mapping), set_default_street])


# Filtering of the addreses
mapping_ammenity = { "biblioteca" :"library",
            "espacio_trabajo" : "coworking_space"
            }

# build list of functions that we will apply to clean our street address
FILTER_AMENITY = gen_apply_filters([get_update_first_word_filter(mapping_ammenity)])


# data cleaning function for postcode
CP_RE = re.compile("^(28|45|05|40|19|16)[0-9]{3}$")

def remove_invalid_postcode(postcode):
    if CP_RE.match(postcode):
        return postcode
    else:
        return None

FILTER_POSTCODE = gen_apply_filters([remove_invalid_postcode])


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node["type"]=element.tag
        # parse attributes
        for k,v in element.attrib.iteritems():
            if k in CREATED:
                if not "created" in node:
                    node["created"]={}
                node["created"][k]=v
            elif k == "lat":
                if not "pos" in node:
                    node["pos"]=[0.0,0.0]
                node["pos"][0]=float(v)
            elif k == "lon":
                if not "pos" in node:
                    node["pos"]=[0.0,0.0]
                node["pos"][1]=float(v)                
            else:
                node[k]=v
        # parse child elements, that are contained in the tag elements with key and value attributes
        for child in element.iter("tag"):
            if "k" in child.attrib:
                if lower.match(child.attrib["k"]):
                    if child.attrib["k"] == "amenity":
                        amenity = FILTER_AMENITY(child.attrib["v"])
                        node["amenity"] = amenity
                    else:
                        node[child.attrib["k"]] = child.attrib["v"]
                elif lower_colon.match(child.attrib["k"]):
                    first , second = child.attrib["k"].split(":")
                    if first == "addr":
                        if not "address" in node:
                            node["address"]={}
                        # apply the previously creted data cleaning functions
                        if second == "street":
                            node["address"][second]=FILTER_STREET(child.attrib["v"])
                        elif second == "postcode":
                            postcode = FILTER_POSTCODE(child.attrib["v"])
                            if postcode:
                                node["address"][second]=postcode                                                 
                        else:
                            node["address"][second]=(child.attrib["v"])
                    else:
                        first = first+":"
                        if not first in node:
                            node[first]={}
                        node[first][second]=child.attrib["v"]                        
                elif problemchars.search(child.attrib["k"]):
                    pass
                else:
                    pass
        for child in element.iter("nd"):
            if "ref" in child.attrib:
                if not "node_refs" in node:
                    node["node_refs"]=[]
                node["node_refs"].append((child.attrib["ref"]))
        element.clear()        
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in, events=["end"]):
            el = shape_element(element)
            if el:
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
            # element.clear()


process_map(OSM_FILE, False)



