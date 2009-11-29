$(function(){
	$('#id_name').keyup(function(){
		var filename = $('#id_name').val().replace(/\s+/g, '_');
		$('#id_slug').val(filename);
	})
	
})
