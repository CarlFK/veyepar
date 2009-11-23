$(function(){
	$('#id_name').keyup(function(){
		var filename = $('#id_name').val().replace(/\s+/g, '_');
		$('#id_slug').val(filename);
	})
	
	$('#login').submit(function(ev){
		$.ajax({
			url: "/accounts/login",
			type: "POST",
            dataType: 'json',
			data: {
				username: $('#username').val(),
                password: $('#password').val()
			},
			success: function(response){
				if(response.error_no){
					$('#error_text').html(response.error_text)
					return;
				}
				$('#login').html('Hi '+ response.fullname )
			}
		})
		ev.preventDefault();
	})
})
