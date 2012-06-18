// JavaScript Document
function init_uncheckall() 
{
	$('#uncheck').click(function () 
	{ 		
		$('.custom_checkbox').each(function(index)
		{		
			$(this).attr('class','custom_checkbox');			
		}); 
	 });
}
function init_checkbox() {
	$('input[type=checkbox]').each(function() {
				$(this).wrap(function() {
					return ($(this).is(':checked')) ? '<div class="custom_checkbox selected" />' : '<div class="custom_checkbox" />';
				});
			});
			
			$('.custom_checkbox input[type=checkbox]').click(function () {
				$(this).parent().toggleClass('selected');
			});
}
function init_gallery() {
				var gallery = $('#images');
				gallery.exposure({controlsTarget : '#controls',
					controls : { prevNext : true, pageNumbers : true, firstLast : false },
					visiblePages : 2,
					slideshowControlsTarget : '#slideshow',
					onThumb : function(thumb) {
						var li = thumb.parents('li');				
						var fadeTo = li.hasClass($.exposure.activeThumbClass) ? 1 : 0.3;
						
						thumb.css({display : 'none', opacity : fadeTo}).stop().fadeIn(50);
						
						thumb.hover(function() { 
							thumb.fadeTo('fast',1); 
						}, function() { 
							li.not('.' + $.exposure.activeThumbClass).children('img').fadeTo('fast', 0.3); 
						});
					},
					onImage : function(image, imageData, thumb) {
						// Fade out the previous image.
						image.siblings('.' + $.exposure.lastImageClass).stop().fadeOut(50, function() {
							$(this).remove();
						});
						
						// Fade in the current image.
						image.hide().stop().fadeIn(50);
 
						// Fade in selected thumbnail (and fade out others).
						if (gallery.showThumbs && thumb && thumb.length) {
							thumb.parents('li').siblings().children('img.' + $.exposure.selectedImageClass).stop().fadeTo(50, 0.3, function() { $(this).removeClass($.exposure.selectedImageClass); });			
							thumb.fadeTo('fast', 1).addClass($.exposure.selectedImageClass);
						}
					},
					onPageChanged : function() {
						// Fade in thumbnails on current page.
						gallery.find('li.' + $.exposure.currentThumbClass).hide().stop().fadeIn('fast');
					}
				});
}

$(document).ready(function() 
{
	init_gallery();
	init_checkbox();
	init_uncheckall();
});