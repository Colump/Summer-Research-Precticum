<template>
<div >
    <el-form ref="form" :model="form" >
  <el-form-item >
    <el-input v-model="form.startPlace" placeholder="Enter journey start location" id="autoComplete"></el-input>
  </el-form-item>
  <div class="swap">
    <el-button icon="el-icon-sort" circle @click="swapEndStart"></el-button>
  </div>
  <el-form-item >
    <el-input v-model="form.endPlace" placeholder="Enter journey end location" id="autoComplete2"></el-input>
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
                {{item.legs[0].steps[1].transit.headsign}}
                <el-button icon="el-icon-search"  circle @click="showInMap(index,item)"></el-button>
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
        const results = directionsService.route({
        origin: this.form.startPlaceLatLng,
        destination: this.form.endPlaceLatLng,
        travelMode: google.maps.TravelMode.TRANSIT,
        provideRouteAlternatives:true
      },
      (response,status) => {
        // console.log(this.form)
        if(status === "OK"){
          directionsRenderer.setDirections(response);
          console.log("这是go下面的数据");
          // console.log(response.routes);



          // response.routes.forEach(function(element) {
          //   const routeInfo = {}
          //   this.form.journeyFromGoogle.route.push(routeInfo);
          //   const steps = []
          //   // const steps = element.legs[0].steps[1].transit.headsign;
          //   // steps.push
          //   // console.log(index);
          //   var info = {index:index};
          //   console.log(info);
          //   // this.form.journeyFromGoogle.push(info);
          // });

          // console.log(this.journeyFromGoogle);
          // this.journeyFromGoogle.push();
          this.form.journeyFromGoogle = response.routes
          console.log("=============================+++++");
          console.log(this.form.journeyFromGoogle);
          console.log("=============================++++");
          // this.$bus.$emit('GetAlljourney',response.routes);
          // console.log(len);
            this.axios.post('/api/get_journey_time.do',JSON.stringify(this.form.journeyFromGoogle)).then(
              (resp) => {
                  let data = resp.data
                  console.log(data)
                  }
            )
          }
        }
      )
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
      }
    }
}
</script>

<style>
.showUserChoiseRoute{
  width: 100%;
  height: 100px;
  display: block;
}
.RouteShow{
  display: block;
  font-size: 10px;
  line-height: 50px;
  height: 50px;
  border-bottom: 1px solid black;
  background-color: pink;

}
.swap{
  display: inline-block;
  height: 30px;
  width: 30px;
  position: absolute;
  left: 239px;
  top: 41px;
}
</style>