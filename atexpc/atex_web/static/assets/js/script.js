$(function(){
	
	var note = $('#note'),
		ts = new Date(2013, 10, 29, 10, 0, 0, 0000),
//		ts = new Date(2013, 10, 28, 23, 11, 30, 0000),
		blackFriday = false;
	
		
	$('#countdown').countdown({
		timestamp	: ts,
		callback	: function(days, hours, minutes, seconds){

			if((new Date()) > ts){
				// The new year is here! Count towards something else.
				// Notice the *1000 at the end - time must be in milliseconds
				// ts = (new Date()).getTime() + 1*1000;
				blackFriday = true;

				setTimeout(function(){
					window.location.href = '/blackfriday';
				}, 1000);
			}

//			console.log('tick ' + blackFriday);			
			var message = "";
			
			message += days + " zile" + ( days==1 ? '':'' ) + ", ";
			message += hours + " ore" + ( hours==1 ? '':'' ) + ", ";
			message += minutes + " minute" + ( minutes==1 ? '':'' ) + " si ";
			message += seconds + " secunde" + ( seconds==1 ? '':'' ) + " <br />";
			
			if(blackFriday){
				message += "pana la Black Friday!";
			}
			else {
				message += "a inceput Black Friday";
			}
			
			note.html(message);
		}
	});
	
});
