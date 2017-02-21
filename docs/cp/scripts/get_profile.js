var getData = (function(){

	var url = "http://localhost:8080/profile"; // the script where you handle the form input.

  $.ajax({
  	dataType: 'json',
	  type: "GET",
	  url: url,
    success: function(profiles)
    {
    		console.log(profiles)
    		for (p in profiles ){
	    		$("#profiles").append(
	    			"<option value ='" + p + "'>" + profiles[p].name + "</option>"
	    		)
	    	}
   	}
 	});
	
})();