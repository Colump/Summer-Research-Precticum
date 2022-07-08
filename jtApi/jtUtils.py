# -*- coding: utf-8 -*-
from flask import Response, stream_with_context
import json
import os, sys
import struct
import time
import zlib


# According to the article here:
#    -> https://towardsdatascience.com/simple-trick-to-work-with-relative-paths-in-python-c072cdc9acb9
# ... Python, if needing to use relative paths in order to make it easier to 
# relocate an application, one can determine the directory that a specific code
# module is located in using os.path.dirname(__file__). A full path name can then
# be constructed by using os.path.join()...
# (the value of __file__ is a string, which is set when module was imported by a loader)
# Application Startup...
jtUtilsParentDir = os.path.dirname(os.path.dirname(__file__))

def loadCredentials():
    """Load the credentials required for accessing the Weather API, Google Maps, etc.

    Returns a JSON object with the required credentials.
    Implemented in a method as Credential storage will be subject to change.
    """
    # Our credentials are just stored in a JSON file (for now)
    # This file is not saved to GitHub and is placed on each EC2 instance
    # by a team member.
    # Load the JSON file
    file = open(os.path.join(jtUtilsParentDir, 'journeytime.json'), 'r')
    credentials = json.load(file)
    file.close  # Can close the file now we have the data loaded...
    return credentials

##########################################################################################
#  Extracts (JSON, .CSV)
##########################################################################################

# 'Module Private' helper function for the various methods that download files...
def _get_next_chunk_size(rows_remain):
    """Calculate the next chunk size for a data set

    Based on the remaining rows and the paramaterised optimimum chunk size
    """
    CHUNK_SIZE = int(loadCredentials()['DOWNLOAD_CHUNK_SIZE'])
    rows_chunk = 0
    if rows_remain > 0:
        if rows_remain >= CHUNK_SIZE:
            rows_chunk  = CHUNK_SIZE
        else:
            rows_chunk  = rows_remain

    return rows_chunk

def query_results_as_compressed_csv(query, name):
    """

    Returns a CSV File with one row per record in the query result set.
    """

    def get_chunk(row_list, first_chunk_tf, query):
        if first_chunk_tf:
            # We need to build the string for the first line of the .csv - the column headers
            col_headers = ''
            for column_desc in query.statement.columns.keys():
                # Each 'column_desc is a dict, with several properties per column.
                col_headers += column_desc + ','
            if len(col_headers) > 1:
                col_headers = col_headers[:-1]

            chunk = col_headers + '\n'
            first_chunk_tf = False
        else:
            chunk = '\n'
        chunk += '\n'.join(row_list)  # csv - join the elements with 'commas'
        return chunk.encode(), first_chunk_tf
    
    def generate(query):
        # I simply could not have implemented this method without:
        #   -> https://stackoverflow.com/questions/44185486/generate-and-stream-compressed-file-with-flask
        # ... as a reference.  I have not researched the Gzip file specification
        # in detail (https://datatracker.ietf.org/doc/html/rfc1952#section-2.2),
        # rather I've copied the values supplied by Martijn Pieters in the
        # stackoverflow article above and adopted his approach to suit my needs.

        # Yield a gzip file header first.
        yield bytes([
            # 0x1f0x8b is the Magic number identifying file type
            # 0x08 is the compression method (deflate)
            0x1F, 0x8B, 0x08, 0x00,  # Gzip file, deflate, no file flags
            *struct.pack('<L', int(time.time())),  # compression start time
            0x02, 0xFF,  # maximum compression, no OS specified
        ])

        # bookkeeping: the compression state, running CRC and total length
        compressor = zlib.compressobj(
            9, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)
        crc = zlib.crc32(b"")

        length = 0
        rows_remain    = query.count()
        rows_chunk     = _get_next_chunk_size(rows_remain)
        row_count      = 0
        row_list       = []
        first_chunk_tf = True
        for row in query:

            # If we build up the string we plan to send by repeatedly appending,
            # we're creating a new string each time. This is quite memory expensive
            # and inefficient.
            # Instead we build a list of strings - which we will later convert to
            # a single string.
            # 'row_list' will be a list of strings...
            row_list.append( '"' + '","'.join([str(value) for value in row.serialize().values()]) + '"')
            row_count += 1

            if row_count >= rows_chunk:
                rows_remain -= rows_chunk  # we've just competed a chunk
                                           # this condition finally exits the loop
                rows_chunk = _get_next_chunk_size(rows_remain)
                # print("Completed a chunk:")
                # print("\tRows Remaining ->", rows_remain)
                # print("\tRows This Chunk ->", rows_chunk)

                chunk, first_chunk_tf = get_chunk(row_list, first_chunk_tf, query)
                chunk_compressed = compressor.compress(chunk)
                if chunk_compressed:
                    yield chunk_compressed
                crc = zlib.crc32(chunk, crc) & 0xFFFFFFFF  # Keep the CRC up to date...
                length += len(chunk)

                row_list = []
                row_count = 0

        # Finishing off, send remainder of the compressed data, and CRC and length
        yield compressor.flush()
        yield struct.pack("<2L", crc, length & 0xFFFFFFFF)

    # Test - do we need 'stream_with_context'?  If I understand the docs correctly
    # then I don't think we do! It's just a method to keep the context alive while
    # streaming).  But time/testing will tell...
    #response = Response(stream_with_context(generate(query, name)), mimetype='application/gzip')
    response = Response(generate(query), mimetype='application/gzip')
    response.headers['Content-Disposition'] = 'attachment; filename=' + name + '.csv.gz'
    return response


def query_results_as_json(query, name):
    """

    Returns a JSON List with one object per record in the query result set.
    """

    def get_chunk(json_list, first_chunk, name):
        if first_chunk:
            chunk = '{\n\"' + name + '\": [\n'
            first_chunk = False
        else:
            chunk = ',\n'
        chunk += ',\n'.join(json_list)
        return chunk, first_chunk
    
    # See...
    #https://stackoverflow.com/questions/19926089/python-equivalent-of-java-stringbuffer
    # ... for some benchmarking on a number of approaches to concatenating lots of strings...
    # json_list=[i.serialize() for i in tripsQuery.all()]
    # return jsonify(json_list)
    def generate(query, name):
        row_count = 0

        # "tripsQuery.all()" is a python list of results
        #rows_remain = len(tripsQuery.all())
        rows_remain = query.count()
        rows_chunk  = _get_next_chunk_size(rows_remain)
        row_count   = 0
        json_list   = []
        first_chunk = True
        for row in query:
            # Don't have to consider empty queries - if we have no results
            # we will never enter this iterator.

            # We removed the indent of four spaces from our generated json. It does look
            # prettier - but it increases download sizes by circa 13% (these extracts are
            # already large)
            #json_list.append( json.dumps(row.serialize(), indent=4) )
            json_list.append( json.dumps(row.serialize()) )
            row_count += 1
            
            # Every time we complete a chunk we yield it and reset out list
            # to an empty list...
            if row_count >= rows_chunk:
                rows_remain -= rows_chunk  # we've jusr competed a chunk
                rows_chunk = _get_next_chunk_size(rows_remain)
                print("Completed a chunk:")
                print("\tRows Remaining ->", rows_remain)
                print("\tRows This Chunk ->", rows_chunk)

                buffer, first_chunk = get_chunk(json_list, first_chunk, name)
                if buffer:
                    yield buffer
                
                json_list = []
                row_count = 0

        # Finishing off, send remainder of the compressed data, and CRC and length
        yield "\n]\n}"  # <- We close the list after the last buffer yield

    return Response(generate(query, name), mimetype='application/json', \
        headers={'Content-disposition': 'attachment; filename=' + name + '.json'})
