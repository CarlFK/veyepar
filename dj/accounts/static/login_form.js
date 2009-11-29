$(function(){
	
	$('#login').submit(function(ev){
		$.ajax({
			url: "/accounts/login",
			type: "POST",
            dataType: 'json',
			data: {
				username: $('#id_username').val(),
                password: $('#id_password').val()
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
