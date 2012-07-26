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
    });

    $('#id_start').datetimepicker({
        dateFormat: 'yy-mm-dd', // note yy is YYYY (i.e. 2009)
        stepHour: 1,
        stepMinute: 15,
        timeFormat: 'hh:mm:ss',
        showSecond: true
    });

    $('#id_duration').timepicker({
        stepMinute: 5,
        timeFormat: 'hh:mm:ss',
        showSecond: true
    });

});
