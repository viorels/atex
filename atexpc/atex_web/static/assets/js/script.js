$(function(){
	
	var note = $('#note'),
		ts = new Date(2013, 10, 29, 10, 0, 0, 0000),
		newYear = true;
	
	if((new Date()) > ts){
		// The new year is here! Count towards something else.
		// Notice the *1000 at the end - time must be in milliseconds
		ts = (new Date()).getTime() + 1*12*60*60*1000;
		newYear = false;
	}
		
	$('#countdown').countdown({
		timestamp	: ts,
		callback	: function(days, hours, minutes, seconds){
			
			var message = "";
			
			message += days + " zile" + ( days==1 ? '':'' ) + ", ";
			message += hours + " ore" + ( hours==1 ? '':'' ) + ", ";
			message += minutes + " minute" + ( minutes==1 ? '':'' ) + " si ";
			message += seconds + " secunde" + ( seconds==1 ? '':'' ) + " <br />";
			
			if(newYear){
				message += "pana la Black Friday!";
			}
			else {
				message += "a inceput Black Friday";
			}
			
			note.html(message);
		}
	});
	
});
