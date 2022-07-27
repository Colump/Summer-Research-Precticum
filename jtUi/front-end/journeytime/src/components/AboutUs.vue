<template>
<div class="text">
  <h1> About Us</h1>
       <p>Journeyti.me is a free to use web application developed by four MSc Computer Science students from University College Dublin. 
         The application gives users a tool to recommend the best bus route or routes between a users desired start and end locations.
         Our prediction engine takes into account a nnumber of factors such as historical bus journey data, weather conditions, traffic data and so on.
      <br>
        A unique selling point of our web application is the development of our own API. While we acknowledge our API will not be as advanced as other APIs such as GTFS and GTFS-R, 
        but we hope that it can be of use to other groups undertaking similar projects in the future. Our API can be accesed through the API page in our main navigation bar. 
      <br>
      <h4>Meet the Team</h4>
      <table>
        <tr>
        <th>Name</th>
        <th>Role</th>
        <th>Background</th>
        </tr>

      <tr>
        <td>Boshen Fan</td>
        <td>Code Lead</td>
        <td>Experience in Java and embedded development</td>
      </tr>
      <tr>
        <td>Yungpeng Chen</td>
        <td>Customer Lead</td>
        <td>Experience in financial and investment</td>
      </tr>
       <tr>
        <td>Tomás Kelly</td>
        <td>Co-ordination Lead</td>
        <td>Experience in OpenVMS</td>
      </tr> 
       <tr>
        <td>Colum Prendiville</td>
        <td>Maintenance Lead</td>
        <td>Experience in project management in the automotive industry</td>
      </tr>
      
      </table>
      
</div>
</template>

<style>
h1{
  font-size: 40px;
  color: black;
}
h4{
  font-size: 30px;
  color: black;
}
p{
  text-align: left;
}
.text{
  font-size: 20px;
  text-align: center;
  padding: 70px 0;
  margin: auto;
  width: 50%;
}
table{
  border-collapse: collapse;
  width: 100%;
}
table td{
  border: 1px solid #ddd;
  padding: 8px;
}
table tr:hover{
  background-color: #ddd;
  }
table th {
  padding-top: 12px;
  padding-bottom: 12px;
  text-align: center;
  background-color: rgb(0, 140, 255);
  color: white;
}
</style>