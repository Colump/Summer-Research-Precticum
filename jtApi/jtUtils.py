# -*- coding: utf-8 -*-
import json
from msilib.schema import File
import os, sys
from flask import Response
from numpy import choose

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

# 'Module Private' helper function for the various methods that download files...
def _get_next_chunk_size(rows_remain):
    """Calculate the next chunk size for a data set

    Based on the remaining rows and the paramaterised optimimum chunk size
    """
    CHUNK_SIZE = int(loadCredentials()['DOWNLOAD_CHUNK_SIZE'])
    print("get_next_chunk_size: rows_remain is ", rows_remain)
    rows_chunk = 0
    if rows_remain > 0:
        if rows_remain >= CHUNK_SIZE:
            rows_chunk  = CHUNK_SIZE
        else:
            rows_chunk  = rows_remain

    return rows_chunk

def download_query_results_as_csv(query, name):
    """

    Returns a CSV File with one row per record in the query result set.
    """

    def get_buffer(row_list, first_chunk, query):
        if first_chunk:
            # We need to build the string for the first line of the .csv - the column headers
            col_headers = ''
            for column_desc in query.statement.columns.keys():
                # Each 'column_desc is a dict, with several properties per column.
                col_headers += column_desc + ','
            if len(col_headers) > 1:
                col_headers = col_headers[:-1]

            buffer = col_headers + '\n'
            first_chunk = False
        else:
            buffer = '\n'
        buffer += '\n'.join(row_list)  # csv - join the elements with 'commas'
        return buffer, first_chunk
    
    def generate(query, name):
        row_count = 0

        # "tripsQuery.all()" is a python list of results
        #rows_remain = len(tripsQuery.all())
        rows_remain = query.count()
        rows_chunk  = _get_next_chunk_size(rows_remain)
        row_count   = 0
        row_list   = []
        first_chunk = True
        for row in query:
            # Don't have to consider empty queries - if we have no results
            # we will never enter this iterator.
            
            # Every time we complete a chunk we yield it and reset out list
            # to an empty list...
            if row_count > rows_chunk:
                print("Starting next chunk...")
                rows_remain -= rows_chunk  # we've jusr competed a chunk
                rows_chunk = _get_next_chunk_size(rows_remain)

                buffer, first_chunk = get_buffer(row_list, first_chunk, query)
                if buffer:
                    yield buffer
                
                row_list = []
                row_count = 0

            # If we build up our the string we plan to send by repeatedly appending,
            # we're creating a new string each time.  This is quite memory expensive
            # and inefficient.
            # Instead we build a list of objects - which we will later convert to a string.
            # 'row_list' will be a list of strings...
            row_list.append( '"' + '","'.join([str(value) for value in row.serialize().values()]) + '"')
            row_count += 1
        
        # At the end - always yield whatever remains in the buffer...
        # We always drop the last comma and close out our json list.
        buffer, first_chunk = get_buffer(row_list, first_chunk, query)
        if buffer:
            yield buffer

    return Response(generate(query, name), mimetype='text/csv', \
        headers={'Content-disposition': 'attachment; filename=' + name + '.csv'})


def download_query_results_as_json(query, name):
    """

    Returns a JSON List with one object per record in the query result set.
    """

    def get_buffer(json_list, first_chunk, name):
        if first_chunk:
            buffer = '{\n\"' + name + '\": [\n'
            first_chunk = False
        else:
            buffer = ',\n'
        buffer += ',\n'.join(json_list)
        return buffer, first_chunk
    
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
            
            # Every time we complete a chunk we yield it and reset out list
            # to an empty list...
            if row_count > rows_chunk:
                print("Starting next chunk...")
                rows_remain -= rows_chunk  # we've jusr competed a chunk
                rows_chunk = _get_next_chunk_size(rows_remain)

                buffer, first_chunk = get_buffer(json_list, first_chunk, name)
                if buffer:
                    yield buffer
                
                json_list = []
                row_count = 0

            # We removed the indend of four spaces from our generated json. It does look
            # prettier - but it increases file sizes by circa 13% (these files are already
            # large)
            #json_list.append( json.dumps(row.serialize(), indent=4) )
            json_list.append( json.dumps(row.serialize()) )
            row_count += 1
        
        # At the end - always yield whatever remains in the buffer...
        # We always drop the last comma and close out our json list.
        buffer, first_chunk = get_buffer(json_list, first_chunk, name)
        if buffer:
            yield buffer + "\n]\n}"  # <- We close the last after the last buffer yield

    return Response(generate(query, name), mimetype='application/json', \
        headers={'Content-disposition': 'attachment; filename=' + name + '.json'})

#         popssible approaches to zip response...

# From first principles:
# ======================
# https://stackoverflow.com/questions/44185486/generate-and-stream-compressed-file-with-flask
# https://stackoverflow.com/questions/44185486/generate-and-stream-compressed-file-with-flask/44387566#44387566

# Using randomer plugin:
# ======================
# https://tilns.herokuapp.com/posts/9b9c0d06d7-generate-and-stream-zipfiles-on-the-fly-with-flask

# Record limit in the configuration File
# Two links for each file - user can choose file or json (file is a csv)
# BUT if the user chooses json for a HUGE data set.... inform the user and then send a json "sample"

