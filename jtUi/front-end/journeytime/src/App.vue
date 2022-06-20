<template>
  <div id="app">
    <div>
      <el-button type="primary" @click.native="hello">button</el-button>
    </div>
  </div>
</template>

<script>


export default {
  name: 'App',
  components: {
    
  },
  methods:{
    hello(){
      console.log("hehehe")
    }
  }

}
</script>

<style>

</style>
