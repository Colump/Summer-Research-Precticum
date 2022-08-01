<template>
<div class="userFormMainDiv">
  <el-form ref="form" :model="form" >
    <el-form-item >
      <span slot="label">Where do you want to go?</span>
      <el-input v-model="form.startPlace" placeholder="Enter starting point" id="autoComplete"></el-input>
    </el-form-item>
    <div class="swap">
      <el-tooltip
    content="Swap start point and destination"
    raw-content>
      <el-button icon="el-icon-sort" circle @click="swapEndStart"></el-button>
      </el-tooltip>
    </div>
    <el-form-item >
      <el-input v-model="form.endPlace" placeholder="Enter destination" id="autoComplete2"></el-input>
    </el-form-item>
    <el-form-item>
      <el-col :span="10">
        <el-date-picker type="date" placeholder="Date" v-model="form.date1" style="width: 100%;"></el-date-picker>
      </el-col>
      <el-col class="line" :span="1">-</el-col>
      <el-col :span="13">
        <el-time-picker placeholder="Time" v-model="form.date2" style="width: 100%;"></el-time-picker>
      </el-col>
    </el-form-item>
    <el-form-item>
      <!-- <el-button type="primary" @click="onSubmit">Go</el-button> -->
      <el-button type="warning" round icon="el-icon-s-open" @click="clearAll">Clear</el-button>
      <el-button type="success" icon="el-icon-check" round @click="onSubmit">Go!</el-button>
    </el-form-item>
  </el-form>
  <div class="showUserChoiseRoute">
    <ul v-if="form.show">
                <!-- 注意每个key要唯一 -->
            <li class="RouteShow" v-for="(item,index) in form.journeyFromGoogle" :key = "index">
              <div class="RouteInfo">
                Take the "{{item.legs[0].steps[1].transit.line.short_name}}" bus
                <!-- {{}} -->
                {{hellofunction(form.backEndRespond.routes[index].steps)}}
                <el-button icon="el-icon-search"  circle @click="showInMap(index,item)"></el-button>
              </div>
              <!-- <el-divider></el-divider> -->
            </li>
    </ul>
  </div>
</div>

</template>

<script>
export default {
    Name:'UserForms',
     data() {
      return {
        form: {
          startPlace: '',
          startPlaceLatLng: '',
          endPlace:'',
          endPlaceLatLng:'',
        //   region: '',
          date1: new Date(),
          date2: new Date(),
          delivery: false,
          journeyFromGoogle: {
              description: "Journeyti.me Step Journey Time Prediction Request",
              title: "Journeyti.me Prediction Request",
              routes:[]
          },
          toBackendInfo: {
            description: "Journeyti.me Step Journey Time Prediction Request",
            title: "Journeyti.me Prediction Request",
            routes:[]
          },
          backEndRespond:{

          },
          show : false,
          flag : 0,
        //   type: [],
        
        //   resource: '',
        //   desc: ''
        }
      }
    },
    mounted(){
      
      // const dir = new google.maps.DirectionsService();
      // const results = dir.route({
      //   origin: '54.1749986272442,-6.34014464532738',
      //   destination: '55.0044762847017,-7.32178170142125',
      //   travelMode: google.maps.TravelMode.TRANSIT
      // })
      // console.log(results)
      const originAuto = new google.maps.places.Autocomplete(
        document.getElementById("autoComplete"),
        // document.getElementById("autoComplete2"),
        {
          bounds:new google.maps.LatLngBounds(
            new google.maps.LatLng(53.3498,-6.2603)
          ),
          componetRestrictions:{ country:"IE"}
        }
      );
      originAuto.addListener("place_changed",()=>{
        this.form.startPlace = originAuto.getPlace().formatted_address
        this.form.startPlaceLatLng=originAuto.getPlace().geometry.location.lat()+','+originAuto.getPlace().geometry.location.lng();
        
        // console.log(this.form.startPlace);
      });
      const desAuto =new google.maps.places.Autocomplete( 
        // document.getElementById("autoComplete"),
        document.getElementById("autoComplete2"),
        {
          bounds:new google.maps.LatLngBounds(
            new google.maps.LatLng(53.3498,-6.2603)
          ),
          componetRestrictions:{ country:"IE"}
        }
      );
      desAuto.addListener("place_changed",()=>{
        // console.log(desAuto.getPlace());
        this.form.endPlace=desAuto.getPlace().formatted_address;
        this.form.endPlaceLatLng = desAuto.getPlace().geometry.location.lat()+','+originAuto.getPlace().geometry.location.lng()
        // console.log(desAuto.getPlace());
      });

      this.$bus.$emit('GetRouteIndex',this.form.flag);

    },
    methods: {
      hellofunction(arr){
        let info = ""
        arr.forEach(function(step){
         info += step.duration.text
        })
        return info;
      },
      showInMap(index,item){
        console.log('++++++++++++++++++++++++++++++++++');
        this.form.flag = index;
        console.log(this.form.flag)
        this.$bus.$emit('GetRouteIndex',this.form.flag);
        console.log('++++++++++++++++++++++++++++++++++++');
        
      },
      onSubmit() {
        // console.log('submit!');
        this.$bus.$emit('GutStartPlace',this.form.startPlaceLatLng);
        this.$bus.$emit('GutEndPlace',this.form.endPlaceLatLng);
        

        this.form.show = !this.form.show;

//      在这里当点击go的时候我们需要获得directionService的数据
        const directionsService = new google.maps.DirectionsService();
        const directionsRenderer = new google.maps.DirectionsRenderer();
        const results = directionsService.route(
          {
            origin: this.form.startPlaceLatLng,
            destination: this.form.endPlaceLatLng,
            travelMode: google.maps.TravelMode.TRANSIT,
            provideRouteAlternatives:true,
            transitOptions:{
              modes: ['BUS'],
            }
          },
          (response,status) => {
            // console.log(this.form)
            if(status === "OK") {
              directionsRenderer.setDirections(response);
              console.log("这是go下面的数据");
              console.log("These are the response routes:", response.routes);

              console.log("Building json package for transmit to prediction server");

              const routes_array = [];
              response.routes.forEach(
                function(route, route_index) {
                  console.log("\tProcessing route:", route_index);
                  // Each route dictionary contains a single key-value pair
                  // The key is 'steps' and the value is a list of step objects.
                  var current_route={};

                  const steps_for_this_route = [];

                  // Loop over all the legs (there should only ever be one...)
                  route.legs.forEach(
                    function(leg, leg_index) {
                      console.log("\t\tProcessing leg:", leg_index);

                      // Loop over all the steps for this leg...
                      // There might be lots - but we're only ever interested in 'TRANSIT steps...
                      leg.steps.forEach(
                        function(step, step_index) {
                          console.log("\t\t\tProcessing step:", step_index);

                          // If this step is a 'TRANSIT' step then we grab the details
                          // ... else we simply ignore it.
                          if(step.travel_mode === 'TRANSIT'){
                            console.log("\t\t\tTransit Step Located - Selecting");
                            var stepForBackEnd = {
                              distance : '',
                              duration:'',
                              transit_details:''
                            };
                            stepForBackEnd.distance = step.distance;  // this is a dictionary
                            stepForBackEnd.duration =  step.duration;  // this is a dictionary
                            stepForBackEnd.transit_details = step.transit;  // this is a dictionary
                            steps_for_this_route.push(stepForBackEnd);
                          }
                        }
                      )  // end of 'for each step'
                    }
                  )  // end of 'for each leg'

                  // Populate the single required key-value pair for a route...
                  current_route['steps'] = steps_for_this_route;
                  // ... and then add that route object to the overall list of routes...
                  console.log("\tFinished processing this route, identified " + steps_for_this_route.length + " TRANSIT steps.");
                  routes_array.push(current_route);
                }
              )  // end of 'for each route'
              // At this point - we should have built all our routes required for
              // our json (the routes_array is the bulk of the work).  Prepare the
              // final object for sending to the prediction engine:
              const prediction_request = {};
              prediction_request["title"] = "Journeyti.me Prediction Request";
              prediction_request["description"] = "Journeyti.me Step Journey Time Prediction Request";
              prediction_request["routes"] = routes_array;
              console.log("Completed Prediction Requeset Objeect: ", prediction_request);
              //this.form.journeyFromGoogle.routes.push(routesInfo) 
              this.form.toBackendInfo = prediction_request;
            } // End of Status OK

            // this.journeyFromGoogle.push();
            this.form.journeyFromGoogle = response.routes;
            console.log("=============================+++++");
            console.log(this.form.journeyFromGoogle);
            console.log("=============================++++");
            console.log("---------------------------------")
            console.log(JSON.stringify(this.form.toBackendInfo))
            console.log("---------------------------------")
            
            // this.$bus.$emit('stopBystopInfo',this.form.toBackendInfo);

            this.axios.post('/api/get_journey_time.do',JSON.stringify(this.form.toBackendInfo),
            { headers: {'Content-Type': 'application/json',}}).then(
                (resp) => {
                  let data = resp.data
                  console.log("---------------------------------****")
                  console.log(data)
                  this.form.backEndRespond = data;
                  this.$bus.$emit('stopBystopInfo',this.form.backEndRespond);
                  console.log("---------------------------------****")
              }
            )
            
          }
        )
          
        // this.journeyFromGoogle.push();
        
        // this.$bus.$emit('GetAlljourney',response.routes);
        // console.log(len);
        
    },
      clearAll(){
        this.form.endPlace ="",
        this.form.endPlaceLatLng ="",
        this.form.startPlace="",
        this.form.startPlaceLatLng =""
      },
      swapEndStart(){
        const temp1 = this.form.endPlace;
        const temp2 = this.form.endPlaceLatLng;
        this.form.endPlace = this.form.startPlace;
        this.form.endPlaceLatLng = this.form.startPlaceLatLng;
        this.form.startPlace = temp1;
        this.form.startPlaceLatLng = temp2;
      }
      
    },
    watch:{
      flag(){
        this.$bus.$emit('GetRoute',this.form.flag);
      },
      journeyFromGoogle(){
        // 先将toBackendInfo传入站到站展示组件（尝试总线是否可以联通）如果这个ok等axios好了之后再去连接data数据
        this.$bus.$emit('stopBystopInfo',this.form.toBackendInfo);
      }
      
            
    }
}
</script>

<style>
.userFormMainDiv{
  width: 100%;
  height: 500px;
}
.showUserChoiseRoute{
  /* position: absolute; */
  /* left: -10px; */
  /* top: 500px; */
  width: 100%;
  height: 200px;
  display: block;
  font-family: element-icons;

}
.RouteShow{
  display: block;
  font-size: 10px;
  line-height: 50px;
  height: 50px;
  /* border-bottom: 1px solid black; */
  /* background-color: pink; */

}
.RouteInfo{
  display: inline;
}
.swap{
    display: inline-block;
    height: 7px;
    width: 6px;
    position: absolute;
    left: 259px;
    top: 79px;
}
label{
  font-family: element-icons;
}
.el-button.is-circle {
    border-radius: 50%;
    padding: 0px;
}
</style>