import xml.etree.ElementTree as ET
# Define input file
OSM_FILE = "madrid_spain.osm" 
# generate a sample File

SAMPLE_FILE_10 = "sample.osm"
SAMPLE_FILE_100 = "sample_100th.osm"


def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag
    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

# generate sample file
# k Parameter: take every k-th top level element
def gen_sample(sample_file,k_th):
    with open(sample_file, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')
        # Write every kth top level element
        for i, element in enumerate(get_element(OSM_FILE)):
            if i % k_th== 0:
                output.write(ET.tostring(element, encoding='utf-8'))
        output.write('</osm>')

# generate a sample file with a tenth of the values for analysis
gen_sample(SAMPLE_FILE_10,10)
# generate a sample files with a 100th of the values for upload
gen_sample(SAMPLE_FILE_100,100)
