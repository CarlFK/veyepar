$(function(){
	$('#id_name').keyup(function(){
		var filename = $('#id_name').val().replace(/\s+/g, '_');
		$('#id_slug').val(filename);
	})
	
	$('#login').submit(function(ev){
		$.ajax({
			url: "/login",
			type: "POST",
			data: {
				username: $('#username').val(),
                username: $('#password').val()
			},
			success: function(response){
				if(response.error_text){
					$('#error_text').html(response.error_text)
					return;
				}
				$('#login').html('Hi '+response.fullname)
			}
		})
		ev.preventDefault();
	})
})
