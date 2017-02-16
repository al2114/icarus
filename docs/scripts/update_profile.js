$("#profileUpdate").click(function() {

    var url = "http://localhost:8080/set_profile"; // the script where you handle the form input.

    var data = form2json($("#profileForm").serialize());
    console.log(data)

    $.ajax({
           type: "POST",
           url: url,
           data: data, // serializes the form's elements.
           success: function(data)
           {
               console.log("Response from server: " + data); // show response from the php script.
           }
         });

    return false; // avoid to execute the actual submit of the form.
});

$("#prof_wrapper").on('click','.prof.prof-sel',function(){
  console.log("hello");
  $(".prof.active").toggleClass('active');
  $(this).toggleClass('active');

  var url = "http://localhost:8080/set_profile"; // the script where you handle the form input.

  var data = JSON.stringify({profile: $(this).attr('id')});
  console.log(data)

  $.ajax({
         type: "POST",
         url: url,
         data: data, // serializes the form's elements.
         success: function(data)
         {
             console.log("Response from server: " + data); // show response from the php script.
         }
  });
  });