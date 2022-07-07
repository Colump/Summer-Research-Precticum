<template>
    <section class="map" ref="map"></section>
    <!-- <div>map</div> -->

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
        StartPlace:'',
        distanation:''
        // center: {lng: -6.24, lat: 53.34},
        // markers: [{
        //   position: {lat: 53.34, lng: -6.24}
        // }]
      }
    },
    mounted(){
      // google.maps.event.addDomListener(window, 'load');
      const map = new google.maps.Map(this.$refs["map"],{
        center: new google.maps.LatLng(53.34,-6.24),
        zoom:13,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      });
      const directionsService = new google.maps.DirectionsService();
      const directionsRenderer = new google.maps.DirectionsRenderer();
      this.$bus.$on('GutStartPlace',(data)=>{

        // geocoder.geocode( { 'address': data}, function(results, status) {
        //   if (status == 'OK') {
        //     console.log(results[0].geometry.location);
        //   } else {
        //     alert('Geocode was not successful for the following reason: ' + status);
        //   }
        // });
        this.StartPlace = data
        // console.log(data)
      })

      this.$bus.$on('GutEndPlace',(data)=>{
        this.distanation = data
        // console.log(data)
      })
      const results = directionsService.route({
        origin: this.StartPlace,
        destination: this.distanation,
        travelMode: google.maps.TravelMode.TRANSIT
      },
      (response,status) => {
        if(status === "OK"){
          directionsRenderer.setDirections(response);
          directionsRenderer.setMap(map);
          console.log("111")
          // console.log(StartPlace);
        }
        console.log(response);
        console.log(status);
        // console.log("222")
        console.log(this.StartPlace);

      }
      )

      
    },
    watch:{
      StartPlace(){
        const map = new google.maps.Map(this.$refs["map"],{
        center: new google.maps.LatLng(53.34,-6.24),
        zoom:13,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      });
        const directionsService = new google.maps.DirectionsService();
      const directionsRenderer = new google.maps.DirectionsRenderer();
        const results = directionsService.route({
        origin: this.StartPlace,
        destination: this.distanation,
        travelMode: google.maps.TravelMode.TRANSIT
      },
      (response,status) => {
        if(status === "OK"){
          directionsRenderer.setDirections(response);
          directionsRenderer.setMap(map);
          console.log("111")
          // console.log(StartPlace);
        }
        console.log(response);
        console.log(status);
        // console.log("222")
        console.log(this.StartPlace);

      }
      )
      },
      distanation(){
        const map = new google.maps.Map(this.$refs["map"],{
        center: new google.maps.LatLng(53.34,-6.24),
        zoom:13,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      });
        const directionsService = new google.maps.DirectionsService();
      const directionsRenderer = new google.maps.DirectionsRenderer();
        const results = directionsService.route({
        origin: this.StartPlace,
        destination: this.distanation,
        travelMode: google.maps.TravelMode.TRANSIT
      },
      (response,status) => {
        if(status === "OK"){
          directionsRenderer.setDirections(response);
          directionsRenderer.setMap(map);
          console.log("111")
          // console.log(StartPlace);
        }
        console.log(response);
        console.log(status);
        // console.log("222")
        console.log(this.StartPlace);

      }
      )
        
      }
    }
}
</script>

<style>
.map{
  width: 100%;
  height: 500px;
}

</style>