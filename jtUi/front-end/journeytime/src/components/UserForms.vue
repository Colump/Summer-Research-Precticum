<template>
<div >
    <el-form ref="form" :model="form" >
  <el-form-item >
    <el-input v-model="form.startPlace" placeholder="origin tpying here!" id="autoComplete"></el-input>
  </el-form-item>
  <el-form-item >
    <el-input v-model="form.endPlace" placeholder="Destination tpying here!" id="autoComplete2"></el-input>
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
    <el-button type="primary" @click="clearAll">Clear All</el-button>
    <el-button type="primary" @click="swapEndStart">Swap</el-button>
  </el-form-item>
  <el-form-item>
    <el-button type="primary" @click="onSubmit">Go!</el-button>
    <!-- <el-button type="primary" @click="onSubmit">Clear All!</el-button> -->
  </el-form-item>
</el-form>

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
        this.form.endPlace=desAuto.getPlace().formatted_address;
        this.form.endPlaceLatLng = desAuto.getPlace().geometry.location.lat()+','+originAuto.getPlace().geometry.location.lng()
        // console.log(desAuto.getPlace());
      });

    },
    methods: {
      onSubmit() {
        console.log('submit!');
        this.$bus.$emit('GutStartPlace',this.form.startPlaceLatLng);
        this.$bus.$emit('GutEndPlace',this.form.endPlaceLatLng);
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
}
</script>

<style>

</style>