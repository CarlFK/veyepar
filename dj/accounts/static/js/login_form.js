// login_form.js

$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

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
            url: "/accounts/login/",
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
