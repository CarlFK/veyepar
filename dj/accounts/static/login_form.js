// login_form.js

function hide_show_login_out() {

    if (auth_name)
    {
        // hide the login form, 
        // show logout, username, and any forms
        $('.logged-out').hide();
        $('.logged-in').show();
        $('#user_name').html(auth_name);
    }
    else
    {
        // hide logout and anything that needs to be logged in
        // show the login form
        $('.logged-in').hide();
        $('.logged-out').show();
    }
}


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
                auth_name=response.fullname;
                hide_show_login_out();
			}
		})
		ev.preventDefault();
	})

	$('#logout').submit(function(ev){
		$.ajax({
			url: "/admin/logout/",
			type: "POST",
			success: function(response){
                auth_name=0;
                hide_show_login_out();
			}
		})
		ev.preventDefault();
	})


// init the page - both login/out is hidden, 
// auth_user is either 0 or username
    hide_show_login_out()

})
