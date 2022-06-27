<template>
<div >
    <el-form ref="form" :model="form" >
  <el-form-item >
    <el-input v-model="form.startPlace" placeholder="origin tpying here!"></el-input>
  </el-form-item>
  <el-form-item >
    <el-input v-model="form.endPlace" placeholder="Destination tpying here!"></el-input>
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
    <el-button type="primary" @click="onSubmit">Go!</el-button>
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
          endPlace:'',
        //   region: '',
          date1: '',
          date2: '',
          delivery: false,
        //   type: [],
        //   resource: '',
        //   desc: ''
        }
      }
    },
    methods: {
      onSubmit() {
        console.log('submit!');
      }
    }

}
</script>

<style>

</style>