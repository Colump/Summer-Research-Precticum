<template>
  <div class="block" id="mainShowRoute">
    <!-- <el-timeline style="height: 1000px; margin-top: 20px;">
      <el-timeline-item style="height: 50px" :hide-timestamp="true"
        v-for="(activity, index) in displayInfo.route"
        :key="index"
        :icon="activity.icon"
        :type="activity.type"
        :color="activity.color"
        :size="activity.size"
        :timestamp="activity.timestamp">
        {{activity.content}}
      </el-timeline-item>
    </el-timeline> -->
    <!--
    First Attempt... straighforward text-based list...
    <ul>
      <li v-for="(item,index) in displayInfo.routes[routeIndex].steps[0].stop_sequence.stops" :key = "index">
          {{item.name}}
          <span slot="label">Time we use is:</span>
          {{item.predicted_time_from_first_stop_s}}
      </li>
    </ul>
     -->
    <!--
    Second Attempt... el-steps *Can't find a way to add a line-break to title!
    <ul>
      <li v-for="(busJourney, index) in listOfBusJourniesForRoute" :key="index">
        {{busJourney.routeName}}
        <el-steps direction="vertical">
          <!-- Valid status values are wait, process, finish, error, success - ->
          <el-step v-for="(stop,index) in busJourney.listOfStops"
            :key="index" status="finish" :title="stop.desc">
          </el-step>
        </el-steps>
      </li>
    </ul>
    -->
    <!--
    Third Attempt... el-steps *Can't find a way to add a line-break to label!
    <el-tree :data="listOfBusJourniesForRoute" :props="defaultProps" @node-click="handleNodeClick"></el-tree>
    -->
    <ul>
      <li v-for="(busJourney, index) in listOfBusJourniesForRoute" :key="index">
        {{busJourney.label}}
        <el-timeline class="busJourneyChildren">
          <el-timeline-item
            v-for="(stop, index) in busJourney.children"
            :key="index"
            :icon="stop.icon"
            :color="stop.colour"
            :timestamp="stop.timestamp"
            class="busJourneyChild">
            {{stop.content}}
          </el-timeline-item>
        </el-timeline>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name:'AsideShowRoute',
  data() {
    return {
      Index:0
    };
  },
  props: [
    "displayInfo","routeIndex"
  ],
  computed: {
    listOfBusJourniesForRoute() {
      let debug_logging = false;
      let listOfBusJourniesForRoute = [];  // We will process raw data for display

      (debug_logging) && console.log('AsideShowRoute.computed.listOfBJFRoute: displayInfo', this.displayInfo)
      (debug_logging) && console.log('AsideShowRoute.computed.listOfBJFRoute: routeIndex', this.routeIndex)
      this.displayInfo.routes[this.routeIndex].steps.forEach(step => {
          let busJourney = {}
          busJourney.label = 'Details for Route: '
          if (step.transit_details.line.short_name != "") {
            busJourney.label += step.transit_details.line.short_name;
          }
          else {
            busJourney.label += step.transit_details.line.name;
          }
          (debug_logging) && console.log('AsideShowRoute.computed.listOfBJFRoute: busJourney.label',  busJourney.label)
          // Get the departure time in 's since the epoch'
          let departureTimeFirstStop = new Date(step.transit_details.departure_time.value);
          busJourney.children = [];
          // Protect against empty list... probably just paranoid but...
          if (step.prediction_status == 'Prediction Attempted - Stop-by-Stop information not available.') {
            let busJourneyStop = {};
            busJourneyStop.content = 'Sorry! We couldn\'t look up the stops for this route'
            busJourneyStop.timestamp = new Date().toLocaleString();
            busJourney.children.push(busJourneyStop)
          }
          else if (step.stop_sequence != null && 'stops' in step.stop_sequence) {
            if (step.stop_sequence.stops != null && step.stop_sequence.stops.length > 0) {
              for (let index in step.stop_sequence.stops) {
                let busStop = step.stop_sequence.stops[index];
                let busJourneyStop = {};
                busJourneyStop.content = busStop.name;
                busJourneyStop.icon = "el-icon-location-information"
                busJourneyStop.colour = "#409EFF";
                let departureTime = new Date(departureTimeFirstStop.getTime());
                departureTime.setSeconds(departureTime.getSeconds() + busStop.predicted_time_from_first_stop_s);
                busJourneyStop.timestamp = departureTime.toLocaleString();
                busJourney.children.push(busJourneyStop)
              }
            }
          }
          else {
            let busJourneyStop = {};
            busJourneyStop.content = 'Hmmm... something went wrong. Please try again later.'
            busJourneyStop.timestamp = new Date().toLocaleString();
            busJourney.children.push(busJourneyStop)
          }
          listOfBusJourniesForRoute.push(busJourney)
        }
      );

      return listOfBusJourniesForRoute
    }
  },
  created() {
    this.$bus.$on('AsideShowRoute_IndexOfRouteToDisplay',(data)=>{
      this.Index = data
    })
  },
  mounted(){
    this.$bus.$on('stopBystopInfo',(data)=>{
      console.log("AsideShowRoute: stopBystopInfo event detected, grabbing activities: ", data)
      this.activities = data
    })
    // No Need for the following - Index already watched (see created() method)
    // this.$bus.$on('Index',(data)=>{
    //   this.Index = data
    // })
  }
}
</script>

<style>
@import url("//unpkg.com/element-ui@2.15.8/lib/theme-chalk/index.css");

#mainShowRoute {
  text-align: left;
}
.busJourneyChildren {
  padding-left: 10px;
}
/* Combined selector required to override default .el-timeline-item styles */
.el-timeline-item.busJourneyChild {
  text-align: left;
  padding-bottom: 6px;
}
</style>