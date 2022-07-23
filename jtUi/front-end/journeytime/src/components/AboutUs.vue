<template>
<div>
       
</div>
</template>

<script>
export default {
    name:'AboutUs',
    data() {
      return {
        form: {
          journeyFromGoogle: [],
          show: false,
        }
      }
    },
    mounted(){
        this.$bus.$on('GetAlljourney',(data)=>{
        this.journeyFromGoogle = data
        // console.log(data)
      })

    },
    watch:{
        journeyFromGoogle(){
        }
    },
    methods:{
        showAllRoute(){
            this.form.show = true;
            this.$bus.$on('GetAlljourney',(data)=>{
                this.journeyFromGoogle = data
            // console.log(data)
            })

        }

    }



}
</script>

<style>

</style>