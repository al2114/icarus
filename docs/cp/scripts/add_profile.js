
        var form_made = false; 

        $(".prof.add").click(function() {

          var n = ($("div[id^='p_custom']").length+1).toString();

          var p = "p_custom" + n;

          $("#prof_wrapper").append(
            "<div id='" + p + "' class='prof prof-form active'>\
                <input type='text' class='prof-name' name='name' value='Custom "+ n +"'/>\
                <div>\
                  <span>\
                    <i class='fa fa-thermometer-three-quarters'></i>\
                    <input type='text' class='prof-temp' name='temp' value='0.0'/>&degC\
                  </span>\
                  <span>\
                    <i class='fa fa-tint' aria-hidden='true'></i>\
                    <input type='text' class='prof-hum' name='hum' value='0'/>%\
                  </span>\
                </div>\
            "
          )

          $(".prof-name[type=text]").focus().select();

          $(".prof-name").keypress(function(){
            form_made = true;
          })
          $(".prof-temp").keypress(function(){
            form_made = true;
          })
          $(".prof-hum").keypress(function(){
            form_made = true;
          })

      });



          var in_div;
          $(".prof-form").hover(function(){ 
              in_div=true;
              console.log(in_div) 
          }, function(){ 
              in_div=false; 
              console.log(in_div) 
          });

$("body").click(function() {
            if(!in_div && form_made){

              var url = "http://localhost:8080/profile"; // the script where you handle the form input.

              var p = $(".prof-form").attr('id');
              var name = $('.prof-name').val();
              var tempval = $('.prof-temp').val();
              var humval = $('.prof-hum').val();

              var data = JSON.stringify({
                "pid": p,
                "name": name,
                "temp": tempval,
                "hum": humval
              });
              console.log(data)

              dataObj = JSON.parse(data)

              $.ajax({
                     type: "POST",
                     url: url,
                     data: data, // serializes the form's elements.
                     success: function(data)
                     {
                         console.log("Response from server: " + data); // show response from the php script.
                        $(".prof-form").remove();
                        form_made = false;
                        $("#prof_wrapper").append(
                          "<div id='" + p + "' class='prof prof-sel'>\
                              <h>"+name+"</h>\
                              <div>\
                                <span>\
                                  <i class='fa fa-thermometer-three-quarters'></i>\
                                  <text>" + tempval + "</text>&degC\
                                </span>\
                                <span>\
                                  <i class='fa fa-tint' aria-hidden='true'></i>\
                                  <text>"+humval+"</text>%\
                                </span>\
                              </div>\
                          "
                        )
                     }
                   });


            }
          });



