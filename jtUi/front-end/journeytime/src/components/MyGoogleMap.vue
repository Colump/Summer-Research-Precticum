<template>
    <div>
      <!-- <el-button type="primary" @click="ShowRoute">getRoute!</el-button> -->
      <section class="map" ref="map"></section>
    <!-- <div>map</div> -->
    </div>
    <!-- <gmap-map
    :center="center"
    :zoom="13"
    style="width: 100%; height: 500px"
  >
    <gmap-marker
      :key="index"
      v-for="(m, index) in markers"
      :position="m.position"
      :clickable="true"
      :draggable="true"
      @click="center=m.position"
    ></gmap-marker>
  </gmap-map> -->
</template>

<script>
export default {
    name:"MyGoogleMap",
    data () {
      return {
        map:null,
        directionsService:null,
        directionsRenderer:null,
        StartPlace:'',
        distanation:'',
        routeIndex:0
        // center: {lng: -6.24, lat: 53.34},
        // markers: [{
        //   position: {lat: 53.34, lng: -6.24}
        // }]
      }
    },
    mounted(){
      // We create a map once the DOM is available...
      this.map = new google.maps.Map(
        this.$refs["map"],
        {
          center: new google.maps.LatLng(53.34,-6.24),
          zoom:13,
          mapTypeId: google.maps.MapTypeId.ROADMAP
        }
      );
      // Create a directionsService and directions renderer ditto...
      this.directionsService = new google.maps.DirectionsService();
      this.directionsRenderer = new google.maps.DirectionsRenderer();
      this.directionsRenderer.setMap(this.map)

      // this.$bus.$on('GutStartPlace',(data)=>{
      //   this.StartPlace = data
      // })
      // this.$bus.$on('GutEndPlace',(data)=>{
      //   this.distanation = data
      // })

      this.$bus.$on('GoogleMaps_IndexOfRouteToDisplay',(data)=>{
        console.log(
          'MyGoogleMaps.mounted(): GoogleMaps_IndexOfRouteToDisplay detected on bus:',
          data
          )
        this.routeIndex = data
      })

      this.$bus.$on('GoogleDirectionsServiceResponse',(data)=>{
        console.log(
          'MyGoogleMaps.mounted(): GoogleDirectionsServiceResponse detected on bus:',
          data
          )
        this.directionsRenderer.setDirections(data)
      })

      // const results = directionsService.route(
      //   {
      //     origin: this.StartPlace,
      //     destination: this.distanation,
      //     travelMode: google.maps.TravelMode.TRANSIT,
      //     transitOptions:{
      //           modes: ['BUS'],
      //     }
      //   },
      //   (response,status) => {
      //     if(status === "OK"){
      //       directionsRenderer.setDirections(response);
      //       console.log('MyGoogleMaps.mounted: directionsService. RouteIndex is:', directionsRenderer.getRouteIndex());
      //       directionsRenderer.setMap(map);
      //       // console.log(StartPlace);
      //     }
      //     console.log(response);
      //     console.log(status);
      //     console.log(this.StartPlace);
      //   }
      // )
    },  // end of mounted:
    methods:{
      // ShowRoute(){
      //   console.log('这里是地图的getroute按钮 MyGoogleMaps.methods.ShowRoute()')
      //   this.$bus.$on('GoogleMaps_IndexOfRouteToDisplay',(data)=>{
      //     this.routeIndex = data
      //   })
      //   // console.log(this.routeIndex)
      // }
    },
    watch:{
      // StartPlace(){
      //   const map = new google.maps.Map(
      //     this.$refs["map"],
      //     {
      //       center: new google.maps.LatLng(53.34,-6.24),
      //       zoom:13,
      //       mapTypeId: google.maps.MapTypeId.ROADMAP
      //     }
      //   );
      //   const directionsService = new google.maps.DirectionsService();
      //   const directionsRenderer = new google.maps.DirectionsRenderer();
      //   directionsRenderer.setRouteIndex(this.routeIndex);

      //   directionsService.route(
      //     {
      //       origin: this.StartPlace,
      //       destination: this.distanation,
      //       travelMode: google.maps.TravelMode.TRANSIT,
      //       provideRouteAlternatives:true,
      //       transitOptions:{
      //             modes: ['BUS'],
      //       }
      //     },
      //     (response,status) => {
      //       if(status === "OK"){
      //         directionsRenderer.setMap(map);
      //         // directionsRenderer.setRouteIndex(0);
      //         console.log("new thingsssss")
      //         console.log(directionsRenderer.getRouteIndex());
      //         directionsRenderer.setDirections(response);
      //         // directionsRenderer2.setRouteIndex(1);
      //         // directionsRenderer2.setDirections(response);
      //         // console.log("response:")
      //         // console.log(response)
      //         // console.log(StartPlace);
      //       }
      //       console.log(response);
      //       console.log(status);
      //       // console.log("222")
      //       console.log(this.StartPlace);
      //     }
      //   )
      // // console.log(results)
      // },
      // distanation(){
      //   const map = new google.maps.Map(
      //     this.$refs["map"],
      //     {
      //       center: new google.maps.LatLng(53.34,-6.24),
      //       zoom:13,
      //       mapTypeId: google.maps.MapTypeId.ROADMAP
      //     }
      //   );
      //   const directionsService = new google.maps.DirectionsService();
      //   const directionsRenderer = new google.maps.DirectionsRenderer();
      //   directionsRenderer.setRouteIndex(this.routeIndex);

      //   const results = directionsService.route(
      //     {
      //       origin: this.StartPlace,
      //       destination: this.distanation,
      //       travelMode: google.maps.TravelMode.TRANSIT,
      //       transitOptions:{
      //             modes: ['BUS'],
      //       }
      //     },
      //     (response,status) => {
      //       if(status === "OK"){
      //         directionsRenderer.setDirections(response);
      //         directionsRenderer.setMap(map);
      //       }
      //       // console.log("this is a new one");
      //       // console.log('data: '+response.routes[0].legs[0].steps[0].travel_mode);
      //       response.routes[0].legs[0].steps.forEach(
      //         function(step) {
      //           if (step.travel_mode === 'TRANSIT') {
      //             var travelJsonForBackEnd = {
      //               busInfo : '',
      //               // name : '',
      //               arrivalStopInfo:'',
      //               endStopInfo:'',
      //               departureTimeInfo:'',
      //               arriveTimeInfo:''

      //             }
      //             travelJsonForBackEnd.busInfo = step.transit.line;
      //             travelJsonForBackEnd.arrivalStopInfo =  step.transit.arrival_stop;
      //             travelJsonForBackEnd.endStopInfo = step.transit.departure_stop;
      //             travelJsonForBackEnd.departureTimeInfo = step.transit.departure_time;
      //             travelJsonForBackEnd.arriveTimeInfo = step.transit.arrival_time;
      //             console.log(travelJsonForBackEnd);
      //           }
      //         }
      //       );
      //     }
      //   )
      // },
      routeIndex(){
        // const map = new google.maps.Map(
        //   this.$refs["map"],
        //   {
        //     center: new google.maps.LatLng(53.34,-6.24),
        //     zoom:13,
        //     mapTypeId: google.maps.MapTypeId.ROADMAP
        //   }
        // );
        // const directionsService = new google.maps.DirectionsService();
        // const directionsRenderer = new google.maps.DirectionsRenderer();
        this.directionsRenderer.setRouteIndex(this.routeIndex);
        console.log('这里路线改变看看是否信息改变 MyGoogleMap.watch.routeIndex:', this.routeIndex)

        // const results = directionsService.route(
        //   {
        //     origin: this.StartPlace,
        //     destination: this.distanation,
        //     travelMode: google.maps.TravelMode.TRANSIT,
        //     provideRouteAlternatives:true,
        //     transitOptions:{
        //       modes: ['BUS'],
        //     }
        //   },
        //   (response,status) => {
        //     if(status === "OK"){
        //       // console.log(directionsRenderer.setDirections(response));
        //       directionsRenderer.setDirections(response);
        //       directionsRenderer.setMap(map);
        //       console.log(
        //         'MyGoogleMap.watch.routeIndex: directionsService.route() response:',
        //         response
        //       )
        //     }
        //     // 22/08/13 TK; Following code does nothing at all???
        //     // // console.log("this is a new one");
        //     // // console.log('data: '+response.routes[0].legs[0].steps[0].travel_mode);
        //     // var travelJsonForBackEnd = {};
        //     // response.routes[0].legs[0].steps.forEach(
        //     //   function(step) {
        //     //     if(step.travel_mode === 'TRANSIT'){
        //     //       travelJsonForBackEnd = {
        //     //         busInfo : '',
        //     //         // name : '',
        //     //         arrivalStopInfo:'',
        //     //         endStopInfo:'',
        //     //         departureTimeInfo:'',
        //     //         arriveTimeInfo:''

        //     //       }
        //     //       travelJsonForBackEnd.busInfo = step.transit.line;
        //     //       travelJsonForBackEnd.arrivalStopInfo =  step.transit.arrival_stop;
        //     //       travelJsonForBackEnd.endStopInfo = step.transit.departure_stop;
        //     //       travelJsonForBackEnd.departureTimeInfo = step.transit.departure_time;
        //     //       travelJsonForBackEnd.arriveTimeInfo = step.transit.arrival_time;
        //     //       // console.log("这是给后端内容的测试！");
        //     //       // console.log(JSON.stringify(travelJsonForBackEnd));
        //     //     }
        //     //   }
        //     // );
        //   }
        // )
      }  // end of routeIndex
    }  // end of watch:
}
</script>

<style>
.map{
  width: 100%;
  height: 100vh;
  margin-bottom: 10%;
}

</style>