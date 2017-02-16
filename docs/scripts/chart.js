var time_d = 5000



var restData = (function() {

  var data = [];

  var now = new Date().getTime();

  var temp_val;
  var hum_val;

  for (var i = 5*60/(time_d/1000)+1; i > 0; i--) {
    //data.push(produceValue(now - i * time_d))
    data.push([now - i * time_d, 0, -0.05])
  }

  setInterval(function() {
    getValue();
  }, time_d);


  function getValue(currentTime) {

    var url = "http://localhost:8080/data"; // the script where you handle the form input.
    $.ajax({
      dataType: 'json',
       type: "GET",
       url: url,
       success: function(server_data)
       {
          temp_val = server_data.temp;
          hum_val = server_data.hum;

          console.log("Response from server " + temp_val.toString())


          $('#t_value').text(((Math.round(temp_val*10)/10).toFixed(1)).toString());

          $('#h_value').text((Math.round(hum_val)).toString());

          hum_val /= 100;

          if (currentTime) {
            now = currentTime;
          } else {
            now = new Date().getTime();
          }

          value = [now, temp_val, hum_val];
          console.log(value);
          data.push(value);

          while (data.length > 60*5/(time_d/1000)+2) {
            data.shift();
          }

       }
     });
    
  }

  function getTempData() {
    tempData = data.map(function(d){ return [d[0],d[1]] });
    console.log(tempData[60][1])
    return tempData;
  } 

  function getHumData() {
    humData = data.map(function(d){ return [d[0],d[2]] });
    console.log(humData[60][1])
    return humData;
  } 

  return {
    getTempData: getTempData,
    getHumData: getHumData
  }
})();

var margin = {
  top: 20,
  right: 20,
  bottom: 30,
  left: 50
},
  height = 200 - margin.top - margin.bottom;
width = 900 - margin.left - margin.right;


$(function() {

  function formatter(time) {
    if ((time.getSeconds() % 60) != 0) {
      return "";
    }
    return d3.time.format('%H:%M:%S')(time);
  }

  var tempdata = restData.getTempData();
  var humdata = restData.getHumData();


  var x = d3.time.scale()
    .domain(d3.extent(tempdata, function(d) {
      return d[0];
    }))
    .range([0, width]);

  var y = d3.scale.linear()
    .domain([10, 40])
    .range([height, 0]);

  var y_hum = d3.scale.linear()
    .domain([0, 1])
    .range([height, 0]);

  var xAxis = d3.svg.axis()
    .scale(x)
    .ticks(d3.time.seconds, 10)
    .tickFormat(formatter)
    .orient("bottom")
    .tickSize(-height);

  var yAxis = d3.svg.axis()
    .scale(y)
    .ticks(5)
    .tickFormat(d3.format(""))
    .orient("left")
    .tickSize(-width);

  var yHumAxis = d3.svg.axis()
    .scale(y_hum)
    .ticks(4)
    .tickFormat(function(n){return n*100})
    .orient("left")
    .tickSize(-width);

  var area = d3.svg.area()
    .x(function(d) {
        return x(d[0]);
    })
    .y0(height)
    .y1(function(d) {
      return y(d[1]);
    });

  var area_hum = d3.svg.area()
    .x(function(d) {
        return x(d[0]);
    })
    .y0(height)
    .y1(function(d) {
      return y_hum(d[1]);
    });

  var line = d3.svg.line()
    .x(function(d) {
      return x(d[0]);
    })
    .y(function(d) {
      return y(d[1]);
    })
    .interpolate("linear");

  var line_hum = d3.svg.line()
    .x(function(d) {
      return x(d[0]);
    })
    .y(function(d) {
      return y_hum(d[1]);
    })
    .interpolate("linear");

  var svg = d3.select("#chart").append("svg")
    .attr("id", "temp_chart")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var svg2 = d3.select("#chart2").append("svg")
    .attr("id", "hum_chart")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    function drawGraph(svg){
      var svgDefs = svg.append('defs');

      var gradient1 = svgDefs.append('linearGradient')
        .attr('id', 'gradient1')
        .attr('x1', '0')
        .attr('x2', '0')
        .attr('y1', '0')
        .attr('y2', '1');

      gradient1.append('stop')
        .attr('class', 'stop-top')
        .attr('offset', '0');
      gradient1.append('stop')
        .attr('class', 'stop-bottom')
        .attr('offset', '1');

      var gradient2 = svgDefs.append('linearGradient')
        .attr('id', 'gradient2')
        .attr('x1', '0')
        .attr('x2', '0')
        .attr('y1', '0')
        .attr('y2', '1');

      gradient2.append('stop')
        .attr('class', 'stop-top')
        .attr('offset', '0');
      gradient2.append('stop')
        .attr('class', 'stop-bottom')
        .attr('offset', '1');

      svg.append("g")
        .attr("class", "border")
        .append("svg:rect")
        .attr("x", 0)
        .attr("y", 0)
        .style("fill", "none")
        .style("shape-rendering", "crispEdges")
        .attr("height", height)
        .attr("width", width);

      svg.append("g")
        .attr("class", "x grid")
        .attr("clipPath", "url(#innerGraph)")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

      var holder = svg.append("defs");
      holder.append("svg:clipPath")
        .attr("id", "innerGraph")
        .append("svg:rect")
        .attr("x", 1)
        .attr("y", 0)
        .style("fill", "gray")
        .attr("height", height)
        .attr("width", width-1);

      holder.append("svg:clipPath")
        .attr("id", "innerGraph2")
        .append("svg:rect")
        .attr("x", 60)
        .attr("y", 20)
        .style("fill", "gray")
        .attr("height", height)
        .attr("width", width);
      }

    drawGraph(svg);
    drawGraph(svg2);


    svg.append("g")
      .datum(tempdata)  
      .attr("clip-path", "url(#innerGraph)")
      .append("svg:path")
      .attr("class", "area")
      .attr("d", area);

    svg.append("g")
      .attr("class", "y grid")
      .call(yAxis)
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end");

    svg.append("g")
      .attr("clip-path", "url(#innerGraph)")
      .append("svg:path")
      .attr("class", "line")
      .attr("d", line(tempdata));

    svg2.append("g")
      .attr("class", "y grid")
      .call(yHumAxis)
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end");

    svg2.append("g")
      .datum(humdata)  
      .attr("clip-path", "url(#innerGraph)")
      .append("svg:path")
      .attr("class", "area")
      .attr("d", area_hum);

    svg2.append("g")
      .attr("clip-path", "url(#innerGraph)")
      .append("svg:path")
      .attr("class", "line")
      .attr("d", line_hum(humdata));

    svg.selectAll("dot")
        .data(tempdata)
      .enter().append("circle")
        .attr("clip-path", "url(#innerGraph)")
        .attr("class", "points")
        .attr("r", 2.5)
        .attr("cx", function(d) { return x(d[0]); })
        .attr("cy", function(d) { return y(d[1]); });

    svg2.selectAll("dot")
        .data(humdata)
      .enter().append("circle")
        .attr("clip-path", "url(#innerGraph)")
        .attr("class", "points")
        .attr("r", 2.5)
        .attr("cx", function(d) { return x(d[0]); })
        .attr("cy", function(d) { return y_hum(d[1]); });

    svg.append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 10 - margin.left)
        .attr("x",0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("Temperature \u00B0C");

    svg2.append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 10 - margin.left)
        .attr("x",0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("Humidity %");

  function update() {
    data_temp = restData.getTempData();
    data_hum = restData.getHumData();

    console.log(data_hum[60][1])
    console.log(data_temp[60][1])

    var svg = d3.select("#temp_chart");
    var svg2 = d3.select("#hum_chart")

    svg.selectAll(".points").remove();
    svg2.selectAll(".points").remove();

    //replot points

    svg.selectAll("dot")
        .data(data_temp)
      .enter().append("circle")
        .attr("clip-path", "url(#innerGraph2)")
        .attr("class", "points")
        .attr("r", 2.5)
        .attr("cx", function(d) { return x(d[0])+50; })
        .attr("cy", function(d) { return y(d[1])+20; });

    svg2.selectAll("dot")
        .data(data_hum)
      .enter().append("circle")
        .attr("clip-path", "url(#innerGraph2)")
        .attr("class", "points")
        .attr("r", 2.5)
        .attr("cx", function(d) { return x(d[0])+50; })
        .attr("cy", function(d) { return y_hum(d[1])+20; });


    //move the temp graph left
    svg.selectAll(".line")
      .attr("d", line(data_temp))
      .attr("transform", null)
      .transition()
      .duration(time_d-50)
      .ease("linear")
      .attr("transform", "translate(" + (x(0) - x(time_d)) + ")");

    svg.selectAll(".points")
      .attr("clip-path", "url(#innerGraph2)")
      .attr("cx", function(d) { return x(d[0])+50; })
      .attr("cy", function(d) { return y(d[1])+20; })
      .attr("transform", null)
      .transition()
      .duration(time_d-50)
      .ease("linear")
      .attr("transform", "translate(" + (x(0) - x(time_d)) + ")")

    svg.selectAll(".area")
      .attr("d", area(data_temp))
      .attr("transform", null)
      .transition()
      .duration(time_d-50)
      .ease("linear")
      .attr("transform", "translate(" + (x(0) - x(time_d)) + ")");

      //move the hum graph right

    svg2.selectAll(".line")
      .attr("d", line_hum(data_hum))
      .attr("transform", null)
      .transition()
      .duration(time_d-50)
      .ease("linear")
      .attr("transform", "translate(" + (x(0) - x(time_d)) + ")");

    svg2.selectAll(".points")
      .attr("clip-path", "url(#innerGraph2)")
      .attr("cx", function(d) { return x(d[0])+50; })
      .attr("cy", function(d) { return y_hum(d[1])+20; })
      .attr("transform", null)
      .transition()
      .duration(time_d-50)
      .ease("linear")
      .attr("transform", "translate(" + (x(0) - x(time_d)) + ")")


    svg2.selectAll(".area")
      .attr("d", area_hum(data_hum))
      .attr("transform", null)
      .transition()
      .duration(time_d-50)
      .ease("linear")
      .attr("transform", "translate(" + (x(0) - x(time_d)) + ")");

    var currentTime = new Date().getTime();
    var startTime = currentTime - 60000*5;
    x.domain([startTime, currentTime]);
    xAxis.scale(x);

        //move the xaxis left
    svg.select(".x.grid")
      .transition()
      .duration(time_d)
      .ease("linear")
      .call(xAxis);
    svg2.select(".x.grid")
      .transition()
      .duration(time_d)
      .ease("linear")
      .call(xAxis);
  }




  setInterval(update, time_d);

});