(function ($) {
    "use strict";
    
    // Dropdown on mouse hover
    $(document).ready(function () {
        function toggleNavbarMethod() {
            if ($(window).width() > 992) {
                $('.navbar .dropdown').on('mouseover', function () {
                    $('.dropdown-toggle', this).trigger('click');
                }).on('mouseout', function () {
                    $('.dropdown-toggle', this).trigger('click').blur();
                });
            } else {
                $('.navbar .dropdown').off('mouseover').off('mouseout');
            }
        }
        toggleNavbarMethod();
        $(window).resize(toggleNavbarMethod);
    });
    


    
    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 100) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });


    // Main News carousel
    $(".main-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        items: 1,
        dots: true,
        loop: true,
        center: true,
    });


    // Tranding carousel
    $(".tranding-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 2000,
        items: 1,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="fa fa-angle-left"></i>',
            '<i class="fa fa-angle-right"></i>'
        ]
    });


    // Carousel item 1
    $(".carousel-item-1").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        items: 1,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="fa fa-angle-left" aria-hidden="true"></i>',
            '<i class="fa fa-angle-right" aria-hidden="true"></i>'
        ]
    });

    // Carousel item 2
    $(".carousel-item-2").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        margin: 30,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="fa fa-angle-left" aria-hidden="true"></i>',
            '<i class="fa fa-angle-right" aria-hidden="true"></i>'
        ],
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            }
        }
    });


    // Carousel item 3
    $(".carousel-item-3").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        margin: 30,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="fa fa-angle-left" aria-hidden="true"></i>',
            '<i class="fa fa-angle-right" aria-hidden="true"></i>'
        ],
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            }
        }
    });
    

    // Carousel item 4
    $(".carousel-item-4").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        margin: 30,
        dots: false,
        loop: true,
        nav : true,
        navText : [
            '<i class="fa fa-angle-left" aria-hidden="true"></i>',
            '<i class="fa fa-angle-right" aria-hidden="true"></i>'
        ],
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            },
            1200:{
                items:4
            }
        }
    });
    
})(jQuery);

// window.open('http://localhost:8000/', 'Order complete', 'width=600, height=600');

// Formats supported: 9xxxxxxxx  09xxxxxxxx 2519xxxxxxxx and +2519xxxxxxxx with spaces, comma, periods, brackets.
// The return value is empty (null) when the format is not supported.
function cleanPhone(num) {
  // First remove any non-digits characters like in 09-12.34.56 78
  var digits =
    num &&
    num
      .replace(/[- )(\.]/g, "")
      // Match leading +2519 or 2519 or 09 or 9 followed by exactly 8 digits
      .match(/^(\+?251|0)?9(\d\d\d\d\d\d\d\d)$/);
  // If the string matched, return with prefix +2519
  if (digits && digits[2]) return "+2519" + digits[2];
  return null;
}
// Function to show a user a phone number as returned from API in local format.
// Simply replaces leading +2519 by 09
function toLocalPhone(to) {
  return to && to.replace(/^\+2519/, "09");
}
