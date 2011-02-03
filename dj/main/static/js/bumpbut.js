 $(document).ready(function() {
   $(".pb").click(function(ev) {
     /* get ID of input box that is right before the button */
     /* alert("getting id"); */
     ibox=$(this).closest("td").prev("td").find("select").attr("id")
     /* bump it */
     x=$('#'+ibox); y = x.val(); x.val(++y);
     /* surpress the submit */
     ev.preventDefault();
   });
 });

