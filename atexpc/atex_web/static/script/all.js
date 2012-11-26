
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

function init_input_hint(form, input, hint) {
    function show_hint_if_empty() {
        if (!input.val()) {
            input.val(hint);
            input.addClass("hint")
        }
    }
    function hide_hint() {
        if (input.val() == hint) {
            input.removeClass("hint")
            input.val("");
        }
    }

    form.submit(function () {
        if (input.val() == hint) {
            input.val("");
            return true; 
        }
    });

    show_hint_if_empty()
    input.focus(hide_hint).blur(show_hint_if_empty)
}

function init_filters() {
	var filter_form = $("form.search");
	var checkboxes = filter_form.find('input[type=checkbox]')
    var dropdowns = filter_form.find('ul.filtrare select')

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

    dropdowns.click(function () {
        if ($(this).hasClass("submit")) {
            filter_form.submit();
        }
    });

	$('.reset_sel_btn').click(function () {
        uncheck_filters();
        return false
    });
}

function toggle_price() {
    var price_checkbox = $('input.checkbox[name="pret"]');
    var price_enabled = price_checkbox.parent().hasClass('selected');
    $(".price_selector input").attr("disabled", !price_enabled);
    return price_enabled;
}

function uncheck_filters() {
	var search_form = $("form.search");
	var checkboxes = search_form.find('input[type=checkbox]')
	checkboxes.each(function () {
		var checkbox = $(this);
		checkbox.parent().removeClass('selected');
		checkbox.removeAttr('checked')
	});
    toggle_price();
	search_form.submit();
}

function show_rezumat() {
	$(".show_rezumat").hide();
	$(".tab_rezumat").show();
	$('.tab_rezumat').click(function(){
		$(".show_rezumat").slideToggle();
	});
}
function calculate_height(){
  getDocHeight = Math.max($(document).height(),$(window).height(),document.documentElement.clientHeight);  
  docHeight = $(document).height();
  viewHeight = $(window).height();  
  bottomHeight = $('.content-bottom').height();
  footerHeight = $('.footer_wrapper').height(); 
  content_wrapper_h = $('.content_wrapper').height();
  header_h = $('.header').height();
  search_bar_h = $('.search_bar').height();
  content_h = content_wrapper_h + header_h + search_bar_h + bottomHeight + footerHeight;  
  viewHeight_new = viewHeight - footerHeight;
  docHeight_new = docHeight - bottomHeight - footerHeight + 30;
  if (viewHeight >= content_h) {
    $('#wrap1').css('min-height', getDocHeight);
    $('#wrap2').css('min-height', viewHeight_new);
  } else {
    $('#wrap1').css('min-height', getDocHeight);
    $('#wrap2').css('min-height', docHeight_new);
  };
}

$(document).ready(function() 
{
	init_gallery();
	init_filters();
	show_rezumat();
    init_beta();
	$('#ui-tabs').tabs({fx:{opacity: 'toggle'}}).tabs('rotate', 5000, true);
	if ($(window).width() > 480) {calculate_height();};

    var search_form = $("form.search");
    var search_input = $(".search_inputs .search");
    var search_hint = search_input.attr("title");
    init_input_hint(search_form, search_input, search_hint);

    var newsletter_form = $(".newsletter form")
    var newsletter_input = newsletter_form.find("input.news_email")
    var newsletter_hint = newsletter_input.attr("title")
    init_input_hint(newsletter_form, newsletter_input, newsletter_hint);
});

function init_beta() {
    $(".login_holder li, .info_cos li, .search_bar .configurator, " +
      ".add_cos_btn, .email-wrapper .email_btn").click(work_in_progress);
}

function work_in_progress() {
    alert("Inca se lucreaza :) . Pentru comenzi apelati 0264-599009 " + 
          "sau trimiteti mail la office@atexpc.ro. Multumim !");
    return false;
}
