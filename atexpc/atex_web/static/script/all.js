
var cart_url = '/cos/';
var get_emails_url = '/login/emails/';

(function($) {
    /* Watch for browser autofill events that do not trigger onchange */
    $.fn.listenForChange = function(options) {
        settings = $.extend({
            interval: 200 // in microseconds
        }, options);

        var jquery_object = this.filter(":input").add(":input",this)
            .filter('[type="text"],[type="radio"],[type="checkbox"],[type="file"],select,textarea');
        var current_focus = null;

        jquery_object
            .focus( function() {
                current_focus = this;
            })
            .blur( function() {
                current_focus = null;
            })
            .change( function () {
                var element = $(this),
                elementValue = ((element.type=='checkbox' || element.type=='radio') && this.checked == false) ? null : element.val();
                element.data('change_listener', elementValue);
            });

        setInterval(function() {
            jquery_object.each(function() {
                var element = $(this),
                    elementValue = ((element.type=='checkbox' || element.type=='radio') && this.checked == false) ? null : element.val();
                // set data cache on element to input value if not yet set
                if (element.data('change_listener') == undefined) {
                    element.data('change_listener', elementValue);
                    return;
                }
                // return if the value matches the cache
                if (element.data('change_listener') == elementValue) {
                    return;
                }
                // ignore if element is in focus (since change event will fire on blur)
                if (this == current_focus) {
                    return;
                }
                // if we make it here, manually fire the change event, which will set the new value
                element.trigger('change');
            });
        }, settings.interval);
        return this;
    };
})(jQuery);

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
    if (!hint) {
        hint = input.attr("title");
    }

    function show_hint_if_empty() {
        if (!input.val()) {
            input.val(hint);
            input.addClass("hint");
        }
    }

    function hide_hint() {
        if (input.val() == hint) {
            input.removeClass("hint");
            input.val("");
        }
    }

    form.submit(function () {
        if (input.val() == hint) {
            input.val("");
            return true;
        }
    });

    show_hint_if_empty();
    input.focus(hide_hint).blur(show_hint_if_empty);
}

function init_filters() {
    var search_form = $("#search_form");
	var filter_form = $("#filter_form");
	var all_checkboxes = $('input[type=checkbox]');
    var left_checkboxes = filter_form.find('input[type=checkbox]');
    var delegate_filters = $('.delegate_filter');

	all_checkboxes.each(function() {
		var checkbox = $(this);
		checkbox.wrap(function() {
			return (checkbox.is(':checked')) ? '<div class="custom_checkbox selected" />'
                                             : '<div class="custom_checkbox" />';
		});
	});
    all_checkboxes.click(function () {
        $(this).parent().toggleClass('selected');
    });

	left_checkboxes.click(function () {
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
	});

    delegate_filters.change(function (e) {
        var filter = $(this);
        var filter_name = filter.attr('name');
        var filter_value = filter.val();
        var delegate = filter_form.find('input[name=' + filter_name + ']');
        delegate.val(filter_value);
        if (filter.is('input[type=checkbox]') && !filter.is(':checked')) {
            delegate.val('');
        }
        if (filter.hasClass("submit")) {
            filter_form.submit();
        }
    });

    function submit_search_filter_form(e) {
        if (filter_form.length) {
            filter_form.submit();
        } else {
            search_form.submit();
        }
        return false;
    }
    $("input#id_cuvinte").keyup(function(e){
        var key_enter = 13;
        if(e.keyCode == key_enter){
            return submit_search_filter_form(e);
        }
    });
    $("input[name=cauta]").click(submit_search_filter_form);

	$('.reset_sel_btn').click(function () {
        uncheck_filters();
        return false;
    });
}

function toggle_price() {
    var price_checkbox = $('input.checkbox[name="pret"]');
    var price_enabled = price_checkbox.parent().hasClass('selected');
    $(".price_selector input").attr("disabled", !price_enabled);
    return price_enabled;
}

function uncheck_filters() {
	var filter_form = $("#filter_form");
	var checkboxes = filter_form.find('input[type=checkbox]');
	checkboxes.each(function () {
		var checkbox = $(this);
		checkbox.parent().removeClass('selected');
		checkbox.removeAttr('checked');
	});
    toggle_price();
	filter_form.submit();
}

function init_rezumat() {
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
  }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
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

function init_csrf() {
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
}

// Cart

function init_cart() {
    $(".add_cos_btn, .add_cos_btn_small").click(function () {
        product_id = $(this).data("product-id");
        add_to_cart(product_id);
        return false;
    });

    cart_form = $("#cart_form");
    function update_cart() {
        $.post(cart_url, cart_form.serialize())
            .success(function (data) {
                on_cart_update(data.cart);
            })
            .error(update_cart_error);
    }
    function remove_row_containing(property) {
        property.closest('div.rand-cos').remove();
    }

    $("input.cart_count").change(function () {
        console.log($(this).val());
        if ($(this).val() === "0") {
            remove_row_containing($(this));
        }
        update_cart();
    });
    $("a.remove_prod").click(function () {
        remove_row_containing($(this));
        update_cart();
        return false;
    });
}

function add_to_cart(product_id) {
    $.post(cart_url, {"method": "add", "product_id": product_id})
        .success(add_to_cart_success)
        .error(update_cart_error);
}

function add_to_cart_success(data, textStatus, jqXHR) {
    on_cart_update(data.cart);
}

function update_cart_error(jqXHR, textStatus, errorThrown) {

}

function on_cart_update(cart) {
    $('.info_cos .cart_count').html(cart.count);
    $('.info_cos .cart_price, span.total_price').html(cart.price.toFixed(2));
    $('span.delivery_price').html(cart.delivery_price.toFixed(2) + " lei");

    $('.show_rezumat').slideDown();

    cart_form = $("#cart_form");
    if (cart_form.length) {
        for (i=0; i<cart.items.length; i++) {
            item = cart.items[i];
            product_id = item.product.id;

            quantity_input = $('input.cart_count[name="product_' + product_id + '_count"]');
            console.log(quantity_input);
            quantity_input.val(item.count);

            quantity_price_li = $('#product_' + product_id).find('li.quantity_price');
            quantity_price_li.text(item.price.toFixed(2) + ' lei');
        }
    }
}

// Login

known_emails_by_username = {};   // 'user' -> ['user@gmail.com', 'user@yahoo.com']

function get_known_emails(username) {
    var known_emails = null;
    if (username !== null && username in known_emails_by_username) {
        known_emails = known_emails_by_username[username]
    }
    return known_emails;
}

function email_username(partial_email) {
    var username = null;
    if (_.contains(partial_email, '@')) {
        var username_domain = partial_email.split('@');
        username = username_domain[0]
    }
    return username;
}

function search_customer(partial_email, is_final) {
    console.debug("searching " + partial_email);
    email_exists = null;
    username = email_username(partial_email);
    if (_.isString(username)) {
        known_emails = get_known_emails(username);
        if (_.isArray(known_emails)) {
            if (_.contains(known_emails, partial_email)) {
                email_exists = true;
            }
            if (!_.some(known_emails, function(email) {
                    return email.indexOf(partial_email) == 0})) {
                email_exists = false;
            }
        }
        else {
            fetch_emails_by_username(username, function() {
                search_customer(partial_email);
            });
        }
    }
    else {
        email_exists = null;
    }
    update_login_form(email_exists, is_final);
    console.debug("searching " + partial_email + " ... " + email_exists);
}

function update_login_form(email_exists, is_final) {
    console.debug("email_exists %s, is_final %s", email_exists, is_final);
    var login_form = $("#loginform");

    password_texts = {
        null: "Parola",
        true: "Client vechi cu parola",
        false: "Client nou cu parola"}
    login_form.find('label[for="logintype_new"]').text(password_texts[email_exists]);

    if (email_exists === true) {
        login_form.find('.signupinput').hide("fast");
        login_form.find('.logininput').show("fast");
    }
    else if (email_exists === false || email_exists === null && is_final) {
        login_form.find('.signupinput').show("fast");
        login_form.find('.logininput').hide("fast");
    }
    else {
        login_form.find('li.signupinput').hide("fast")
        login_form.find('input[type="submit"].logininput').show("fast");
        login_form.find('input[type="submit"].signupinput').show("fast");
    }
}

function fetch_emails_by_username(username, done_callback) {
    $.get(get_emails_url + username)
        .success(function (data) {
            fetched_emails = data.emails;
            known_emails_by_username[username] = fetched_emails;
            if (done_callback) {
                done_callback();
            }
        });
}

function init_login() {
    var login_form = $("#loginform");
    if (!login_form.length) return;

    login_form.listenForChange();
    login_form.find("input[name='username']").on("keyup change blur", function(e) {
        var partial_email = $(e.target).val();
        var is_final = e.type == "blur";
        search_customer(partial_email, is_final);
    }).change();

    // name fields hint
    var login_form_inputs = login_form.find('input[name*="_name"]')
                                      .each(function (i, form_input) {
                                          init_input_hint(login_form, $(form_input));
                                      });

    // visible password
    $('#show_password').change(function() {
        var isChecked = $(this).prop('checked');
        if (isChecked) {
            $('#masked_password').hide();
            $('#readable_password').val($('#masked_password').val())
            $('#readable_password').show();
        }
        else {
            $('#masked_password').show();
            $('#readable_password').hide();
        }
    });

    $('#readable_password').click(function() {
        $('#show_password').prop('checked', false).change().parent().toggleClass('selected');
        $('#masked_password').focus();
    })
}

function init_order() {
    var order_form = $("#orderform");
    if (!order_form.length) return;

    var customer_type_input = order_form.find('input[name="customer_type"]')
    customer_type_input.change(function (e) {
        var customer_type = customer_type_input.filter(':checked').val();
        $('.info_type_f, .info_type_j, .info_type_o').hide();
        $('.info_type_' + customer_type).show("fast");
    });
    customer_type_input.change();

    var cif_input = $('.company_cif')
    cif_input.change(function (e) {
        var cif = cif_input.filter(':visible').val();
        if (typeof cif !== "undefined" && cif.length > 0) {
            $.ajax({
                type: 'get',
                url: '/company_info/' + cif,
                dataType: 'json',
                success: function(data) {
                    order_form.find('input[name="company"]').val(data['name']);
                    order_form.find('input[name="city"]').val(data['city']);
                    order_form.find('input[name="county"]').val(data['state']);
                    order_form.find('textarea[name="address"]').val(data['address']);
                    order_form.find('input[name="regcom"]').val(data['registration_id']);
                    // inregistrat in scopuri TVA: data['vat'] == '1'
                }
            });
        }
    });

    var delivery_input = order_form.find('input[name="delivery"]');
    delivery_input.change(function (e) {
        var delivery = delivery_input.filter(':checked').val();
        order_form.find('.delivery_no').hide();
        order_form.find('.delivery_other').hide(); 
        if (delivery == 'no') {
            order_form.find('.delivery_no').show('fast');
        }
        else if (delivery == 'other') {
            order_form.find('.delivery_other').show('fast'); 
        }
    });
    delivery_input.change();

    // fields hint
    var login_form_inputs = order_form.find('input[type="text"], textarea')
                                      .each(function (i, form_input) {
                                          init_input_hint(order_form, $(form_input));
                                      });

    $("a.continua").click(function() {
        order_form.submit();
        return false;
    })
}

function init_confirm() {
    var confirm_form = $("#confirmform");
    if (!confirm_form.length) return;

    $("a.confirma").click(function() {
        confirm_form.submit();
        return false;
    })
}

$(document).ready(function() {
	init_gallery();
	init_filters();
	init_rezumat();
    init_csrf();
    init_cart();
    init_login();
    init_order();
    init_confirm();
	$('#ui-tabs').tabs({fx:{opacity: 'toggle'}}).tabs('rotate', 5000, true);
	if ($(window).width() > 480) {
        calculate_height();
    }

    var search_input = $(".search_inputs .search");
    init_input_hint($("#search_form"), search_input);
    init_input_hint($("#filter_form"), search_input);

    var newsletter_input = $("input.news_email");
    init_input_hint($(".newsletter form"), newsletter_input);
});

