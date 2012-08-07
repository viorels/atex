
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

function init_search_input() {
    var search_form = $("form.search");
    var search_input = $(".search_inputs .search");
    var search_hint = search_input.attr("title");

    function show_search_hint_if_empty() {
        if (!search_input.val()) {
            search_input.val(search_hint);
            search_input.addClass("hint")
        }
    }
    function hide_search_hint() {
        if (search_input.val() == search_hint) {
            search_input.removeClass("hint")
            search_input.val("");
        }
    }

    search_form.submit(function () {
        if (search_input.val() == search_hint) {
            search_input.val("");
            return true; 
        }
    });

    show_search_hint_if_empty()
    search_input.focus(hide_search_hint).blur(show_search_hint_if_empty)
}

function init_filters() {
	var filter_form = $("form.filters");
	var checkboxes = filter_form.find('input[type=checkbox]')

	function toggle_price() {
		var price_checkbox = $('input.checkbox[name="pret"]');
		var price_enabled = price_checkbox.parent().hasClass('selected');
		$(".price_selector input").attr("disabled", !price_enabled);
		return price_enabled;
	}

	checkboxes.each(function() {
		var checkbox = $(this)
		checkbox.wrap(function() {
			return (checkbox.is(':checked')) ? '<div class="custom_checkbox selected" />'
											 : '<div class="custom_checkbox" />';
		});
	});
	
	checkboxes.click(function () {
		$(this).parent().toggleClass('selected');
		if ($(this).hasClass("submit")) {
			filter_form.submit();
		}
		else if ($(this).attr("name") == "pret") {
			price_enabled = toggle_price();
			if (!price_enabled) {
				filter_form.submit();
			}
		}
	});

	toggle_price();
	$(".price_selector input.price_search").click(function () {
		filter_form.submit();
	})

	$('.reset_sel_btn').click(uncheck_filters);
}

function uncheck_filters() {
	var filter_form = $("form.filters");
	var checkboxes = filter_form.find('input[type=checkbox]')	
	checkboxes.each(function () {
		var checkbox = $(this);
		checkbox.parent().removeClass('selected');
		checkbox.removeAttr('checked')
	});
	filter_form.submit();
}

function show_rezumat() {

	$(".show_rezumat").hide();
	$(".tab_rezumat").show();
	$('.tab_rezumat').click(function(){
		$(".show_rezumat").slideToggle();
	});
}

$(document).ready(function() 
{
	init_gallery();
    init_search_input();
	init_filters();
	show_rezumat();
});
