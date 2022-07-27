import pickle
from math import radians, cos, sin, asin, sqrt
import pandas as pd

f= open("D:\group\comp47360_group3_raduno\jtApi\pickles\JourneyPrediction-r0-s1.pickle", 'rb')
usepickle = pickle.load(f)
f.close()
#import os, sys
JourneyPrediction=usepickle
print(type(JourneyPrediction))
lineid=JourneyPrediction.get_route_shortname_pickle_exists()
print(lineid)
list= JourneyPrediction.get_step_stpps()
print(type(list))
print(type(list[0]))
StepStop=list[0]
print(type(StepStop.get_stop()))
z1=StepStop.get_stop()
print(z1.stop_position)
z2=StepStop.get_shape_dist_traveled()
print(z2)
print('time is')
print(JourneyPrediction.get_planned_duration_s())
#z=t[0].get_stop_sequence()
#print(z)
#print('JT_Utils: Main Method')
#pickles_dir='pickles'
#pickle_path= os.path.join(jt_utils_dir, pickles_dir)

#with (open(os.path.join(pickle_path, 'JourneyPrediction-r0-s0.pickle'), "rb")) as jp_pickle:
      #  journey_pred = pickle.load(jp_pickle)
        # # Call a function to get the predicted journey time for this step.
      #  journey_pred = predict_journey_time(journey_pred)



import pickle
import numpy as np
# https://www.csdn.net/tags/OtDaggysMTU0MjQtYmxvZwO0O0OO0O0O.html
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r
def predict_journey_time_usestopmodel(journey_prediction):
    # # load the prediction model
# end_to_end_filepath='/pickles/end_to_end/'+lineid+".pickle"
    pickepath="" #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    f= open("D:\group\comp47360_group3_raduno\jtApi\pickles\stop_to_stop\stoptostop.pickle", 'rb')
    
    stop_pickle = pickle.load(f)
    f.close()

    #f = open(pickepath,'rb')
    #f= open(os.path.join(jt_utils_dir, end_to_end_filepath), 'r')
   # stop_pickle = pickle.load(f)
    #f.close()

    duration = journey_prediction.get_planned_duration_s()
    time = journey_prediction.get_planned_departure_datetime()
    hour=time.hour
    week=time.isoweekday()
   # month=time.month
   # lineid=journey_prediction.get_route_shortname()
    temperature=weather_information(hour)
    #temperature=20
    week_sin= np.sin(2 * np.pi * week/6.0)
    week_cos = np.cos(2 * np.pi * week/6.0)
    hour_sin = np.sin(2 * np.pi * hour/23.0)
    hour_cos  = np.cos(2 * np.pi * hour/23.0)
  #  month_sin = np.sin(2 * np.pi * month/12.0)
  #  month_cos  = np.cos(2 * np.pi * month/12.0)

    list= journey_prediction.get_step_stpps()


    total_dis=0.001
    total_time=0

    for index,stop in enumerate(list):
          #total_dis=stop.get_shape_dist_traveled()+total_dis
          stoppre=list[index-1].get_stop()
          stopnow=stop.get_stop()
        
          stoppre_lat = stoppre.stop_lat
          stoppre_lon = stoppre.stop_lon 
          stoppre_dist_from_cc = stoppre.dist_from_cc

          stopnow_lat = stopnow.stop_lat
          stopnow_lon = stopnow.stop_lon 
          stopnow_dist_from_cc = stopnow.dist_from_cc

          dis_twostop=haversine(stopnow_lon, stopnow_lat, stoppre_lon, stoppre_lat)
          total_dis=total_dis+dis_twostop
    for index,stop in enumerate(list):
      if index != 0:
        stoppre=list[index-1].get_stop()
        stopnow=stop.get_stop()
        
        stoppre_lat = stoppre.stop_lat
        stoppre_lon = stoppre.stop_lon 
        stoppre_dist_from_cc = stoppre.dist_from_cc

        stopnow_lat = stopnow.stop_lat
        stopnow_lon = stopnow.stop_lon 
        stopnow_dist_from_cc = stopnow.dist_from_cc

        dis_twostop=haversine(stopnow_lon, stopnow_lat, stoppre_lon, stoppre_lat)
        plantime_partial=duration*(dis_twostop/total_dis)
        #dic_list = [{'PLANNED_JOURNEY_TIME':duration,'HOUR':10,'temp':6.8,'week':6,'Month':1}]
        dic_list = [{'PLANNED_JOURNEY_TIME':plantime_partial,	'dis_twostop':dis_twostop,'dis_prestop_city':stoppre_dist_from_cc,'dis_stopnow_city':stopnow_dist_from_cc,
        	'temp':temperature,'week_sin':week_sin,'week_cos':week_cos,'hour_sin':hour_sin,'hour_cos':hour_cos}]  

        input_to_pickle_data_frame = pd.DataFrame(dic_list)
        # throw the dataframe into model and predict time 
        predict_result=stop_pickle.predict(input_to_pickle_data_frame)
        total_time=predict_result+total_time
        print(predict_result)
        journey_prediction.set_predicted_duration_s(total_time)   
    return journey_prediction  # Return the updated rediction_request
    # return total_time

ll=predict_journey_time_usestopmodel(JourneyPrediction)
print(type(ll))
print(ll)




