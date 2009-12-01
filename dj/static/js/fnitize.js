$(function(){
	
	$('#id_name').blur(function(){
		var val = $('#id_name').val();
		val = val.replace(/\s+/g, '_');
		val = val.replace(/\s+/g, '_');
		if (!$('#id_slug').val())
        {
            $('#id_slug').val(val);
        }
	})
	
})
