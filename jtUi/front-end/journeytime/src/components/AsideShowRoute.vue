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
                
            <li v-for="(item,index) in displayInfo.routes" :key = "index">
                {{item.steps[0].distance.value}}
            </li>
    </ul>
    {{displayInfo.routes[0].steps[0].distance.value}}
  </div>
</template>

<script>
export default {
    name:'AsideShowRoute',
    data() {
      return {
        // displayInfo:{},
        activities: [{
          content: 'stop1',
        }, {
          content: 'stop2',
        }, {
          content: 'stop3',
        }, {
          content: 'stop4',
        }]
      };
    },
    props: {
      displayInfo: Object,
      required: true
    },
    mounted(){
      this.$bus.$on('stopBystopInfo',(data)=>{
        this.activities = data
        console.log("stop by stop model ======")
        console.log(data)
      })
    },
    created() {
      // this.$bus.$on('stopBystopInfo',(data)=>{
      //   console.log("信息传递组件方法启动")
      //   this.displayInfo = data
      // })

      
    },
}
    

</script>

<style>
.el-timeline-item__wrapper {
    position: relative;
    padding-left: 28px;
    top: -94px;
}
</style>