function form2json(serializedData) {
    var ar1 = serializedData.split("&");
    var json = "{";
    for (var i = 0; i<ar1.length; i++) {
        var ar2 = ar1[i].split("=");
        json += i > 0 ? ", " : "";
        json += "\"" + ar2[0] + "\" : ";
        json += "\"" + (ar2.length < 2 ? "" : ar2[1]) + "\"";
    }
    json += "}";
    return json;
}

var getInfo = (function(){

  var url = "http://localhost:8080/"; // the script where you handle the form input.

  $.ajax({
  	dataType: 'json',
	  type: "GET",
	  url: url+"profile",
    success: function(profiles)
    {		
		console.log("SUPP")
		console.log(profiles)
		for (p in profiles ){
    		console.log(p);
    		$("#prof_wrapper").append(
    			"<div id='" + p + "' class='prof prof-sel'>\
    			    <div class='" + p + " bg'></div>\
    			    <h>"+profiles[p].name+"</h>\
    			    <div>\
			          <span>\
			            <i class='fa fa-thermometer-three-quarters'></i>\
			            <text>" + profiles[p].temp + "</text>&degC\
			          </span>\
			          <span>\
			            <i class='fa fa-tint' aria-hidden='true'></i>\
			            <text>"+profiles[p].hum+"</text>%\
			          </span>\
    			    </div>\
    			"
    		)
    	}
   	}
  });

	$.ajax({
		dataType: 'json',
	  type: "GET",
	  url: url+"switch",
	    success: function(state) {
	    		console.log("state: " + state)
	    		$( "#switch" ).addClass(state?"on":"off").css("background-color",state?"#31b80d":"#888");
			    $("#switch-inner").css('margin-left',state?'15px':'1px');

	   	}
 	});
	
})();