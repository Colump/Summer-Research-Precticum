import sys
from google.transit import gtfs_realtime_pb2
import requests
import json
from jtUtils import loadCredentials

# NOTE
# If you're here you've probably already inspected the documentation at:
#   -> https://developer.nationaltransport.ie/api-details#api=gtfsr&operation=gtfsr
# Make sure you click the "Try It" button on the same page.  That is where I spotted
# the required headers that allow you to specify cache control, api-key etc.

# ALSO if I add '?format=json' to the url i get an invalid wire type error. It's
# as though I'm already being fed a "jsonified" version of the ?binary? feed.
# Haven't yet found more supporting documentatio/information.  I would imagine
# the "Right Solution" is to find the protobuf endpoint (there must be one??).
# We might have to contact the NTA for that??

def gtfsr():
    """ Downloads an entire GTFS-R feed from the NTA and saves it to disk
    
    We could cache this info. We could use this info.  But HOW!?!?!?!?
    """
    credentials = loadCredentials()

    nta_gtfsr_api_url = credentials['nta-gtfs']['gtfsr-api-url']
    print(nta_gtfsr_api_url)
    nta_gtfsr_reqd_hdrs = {
        "Cache-Control": "no-cache",
        "x-api-key": credentials['nta-gtfs']['gtfsr-api-key-primary']
        # Do we need the secondary key??  How do I specify it???
    }

    feed = gtfs_realtime_pb2.FeedMessage()
    abort_counter = 0
    max_abort_counter = 200
    gtfsr_log = open("sample_gtfsr_trip_update_feed_complete.txt", "w")
    
    with requests.get(nta_gtfsr_api_url, headers=nta_gtfsr_reqd_hdrs) as response:

        feed.ParseFromString(response.content)
        # for entity in feed.entity:
        #     gtfsr_log.write(str(entity))
        #     abort_counter += 1
        #     # if entity.HasField('trip_update'):
        #     #     #print("TRIP UPDATE!!!!!!!!!!!!!!!!!!")
        #     #     #print(entity.trip_update)
        #     #     pass
        #     # else:
        #     #     print("... SOMETHING ELSE.... !!!!!!!!!!!!!!!!!!")
        #     #     print(entity)

        #     if (abort_counter >= max_abort_counter):
        #         print("=======================================================")
        #         print(str(max_abort_counter) + " entities read - that's enough for now!! Aborting...")
        #         break

        for entity in feed.entity:
            gtfsr_log.write(str(entity))

    gtfsr_log.close()

    return

def main():
    """
    """
    print('This program will open the NTA GTFS-R feed and spit it out to the console')
    print('If there is useful ')
    print('')

    gtfsr()

    print('\r\nFinished!')
    sys.exit()

if __name__ == '__main__':
    main()
