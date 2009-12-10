$(function(){
    
    $('#id_name').blur(function(){
        var val = $('#id_name').val();
        // val = val.replace(/\s+/g, '_');
        val = URLify(val,300);
        val = val.replace(/-/g, '_');
        if (!$('#id_slug').val())
        {
            $('#id_slug').val(val);
        }
    })
    
    // $('#id_end').datepicker();

    $('#id_end').html( $('#id_end').html() + 'foo' );

    $('#id_start').html( '<a href="javascript: NewCssCal(\'id_start\',\'yyyymmdd\',\'arrow\',true,24,false)">X</a>' + $('#id_start').html() );

})
