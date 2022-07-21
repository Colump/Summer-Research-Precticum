<template>
<div>
        <el-button type="primary" @click="showAllRoute">show</el-button>
        <ul v-if="form.show">
            <!-- 注意每个key要唯一 -->
            <li v-for="(item,index) in form.journeyFromGoogle" :key = "index">{{item}}</li>
        </ul>
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