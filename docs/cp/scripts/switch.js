$("#switch").click(function() {

  if($(this).attr("class") === 'on'){
    $(this).removeClass().addClass('off').css("background-color","#888");
    $("#switch-inner").css('margin-left','1px');
  } else {
    $(this).removeClass().addClass('on').css("background-color","#31b80d");
    $("#switch-inner").css('margin-left','15px');
  }

  console.log($(this).attr("class"))

  var url = "http://localhost:8080/switch"; // the script where you handle the form input.

  $.ajax({
      type: "POST",
      url: url,
      data: $("#switch").attr('class'), // serializes the form's elements.
      success: function(data)
      {
        console.log("Response from server: " + data); // show response from the php script.
      }
  });

  return false; // avoid to execute the actual submit of the form.
});