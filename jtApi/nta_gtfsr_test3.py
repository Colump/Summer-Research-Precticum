import sys
from google.transit import gtfs_realtime_pb2
import requests
from jtUtils import loadCredentials


def gtfsr():
    """
    """
    credentials = loadCredentials()

    nta_gtfsr_api_url = credentials['nta-gtfsr']['api-url']
    print(nta_gtfsr_api_url)
    nta_gtfsr_reqd_hdrs = {
        "Cache-Control": "no-cache",
        "x-api-key": credentials['nta-gtfsr']['api-key-primary']
        # Do we need the secondary key??  How do I specify it???
    }

    feed = gtfs_realtime_pb2.FeedMessage()
    abort_counter = 0
    with requests.get(nta_gtfsr_api_url, headers=nta_gtfsr_reqd_hdrs) as response:
        feed.ParseFromString(response.content)
        for entity in feed.entity:
            abort_counter += 1
            if entity.HasField('trip_update'):
                print("TRIP UPDATE!!!!!!!!!!!!!!!!!!")
                print(entity.trip_update)
            else:
                print("... SOMETHING ELSE.... !!!!!!!!!!!!!!!!!!")
                print(entity)

            if (abort_counter == 200):
                print("=======================================================")
                print("200 entities read - that's enough for now!! Aborting...")
                break

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
