<template>
  <div class="block">
    <!-- <el-timeline style="height: 1000px; margin-top: 20px;">
      <el-timeline-item style="height: 50px" :hide-timestamp="true"
        v-for="(activity, index) in displayInfo.route"
        :key="index"
        :icon="activity.icon"
        :type="activity.type"
        :color="activity.color"
        :size="activity.size"
        :timestamp="activity.timestamp">
        {{activity.content}}
      </el-timeline-item>
    </el-timeline> -->

    <ul>
                
            <li v-for="(item,index) in displayInfo.routes[routeIndex].steps[0].stop_sequence.stops" :key = "index">
                {{item.name}}
            </li>
    </ul>
    <!-- {{routeIndex}} -->
    <!-- {{displayInfo.routes[0].steps[0].distance.value}} -->
  </div>
</template>

<script>
export default {
    name:'AsideShowRoute',
    data() {
      return {
        Index:0
      };
    },
    props: [
      
      "displayInfo","routeIndex"
    ],
    mounted(){
      this.$bus.$on('stopBystopInfo',(data)=>{
        this.activities = data
        console.log("stop by stop model ======")
        console.log(data)
      })

       this.$bus.$on('Index',(data)=>{
        this.Index = data
      })
    },
    created() {
      this.$bus.$on('Index',(data)=>{
        this.Index = data
      })
    },
}
    

</script>

<style>
.el-timeline-item__wrapper {
    position: relative;
    padding-left: 28px;
    top: -94px;
}
.el-timeline-item{
  font-family: element-icons;
}
</style>