<template>
  <div>
    <button @click="getStop">get stop information</button>
  </div>
</template>

<script>
import axios from 'axios'
export default {
    name:'StopsData',
    methods:{
        getStop(){
            axios.get('http://localhost:8080/stops').then(
                response => {
                    console.log('getTheStopSuccessful',response.data)
                },
                error=>{
                    console.log('false',error.message)
                }
            )
        }
    }

}
</script>

<style>

</style>