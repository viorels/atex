$(document).ready(function(){

    //open pop box
    $('#buy-mb').click(function(){
        $('.pop-wrapper').fadeIn(200);
        $('.pop-mb').fadeIn(200);
    });
    $('#buy-monitor').click(function(){
        $('.pop-wrapper').fadeIn(200);
        $('.pop-monitor').fadeIn(200);
    });
    $('.see-contact-list').click(function(){
        $('.pop-wrapper').fadeIn(200);
        $('.pop-contact').fadeIn(200);
        $('.pop-faq').fadeOut(200); // link from faq to contact list
    });
    $('.see-faq').click(function(){
        $('.pop-wrapper').fadeIn(200);
        $('.pop-faq').fadeIn(200);
    });
    
    //close pop box
    $('.pop-monitor .close').click(function(){
        $('.pop-wrapper').fadeOut(200);
        $('.pop-monitor').fadeOut(200);
    });
    $('.pop-mb .close').click(function(){
        $('.pop-wrapper').fadeOut(200);
        $('.pop-mb').fadeOut(200);
    });
    $('.pop-contact .close').click(function(){
        $('.pop-wrapper').fadeOut(200);
        $('.pop-contact').fadeOut(200);
    });
    $('.pop-faq .close').click(function(){
        $('.pop-wrapper').fadeOut(200);
        $('.pop-faq').fadeOut(200);
    });
    $('.mask').click(function(){
        $('.pop-wrapper').fadeOut(200);
        $('.pop-mb').fadeOut(200);
        $('.pop-monitor').fadeOut(200);
        $('.pop-contact').fadeOut(200);
        $('.pop-faq').fadeOut(200);
    });


    //pop size
    var vph = $(window).height();
    var hvph = vph * 0.9;
    $('.pop-mb').css('height',hvph);
    $('.pop-monitor').css('height',hvph);
    $('.pop-contact').css('height',hvph);
    $('.pop-faq').css('height',hvph);

    $( window ).resize(function() {
    var vph = $(window).height();
    var hvph = vph * 0.9;
    $('.pop-mb').css('height',hvph);
    $('.pop-monitor').css('height',hvph);
    $('.pop-contact').css('height',hvph);
    $('.pop-faq').css('height',hvph);
    });


});//end ready







