/**
* PHP Email Form Validation - v2.0
* URL: https://bootstrapmade.com/php-email-form/
* Author: BootstrapMade.com
*/
!(function($) {
  "use strict";

  //Newsletter
  $('form.subscribeForm').submit(function () {
    console.log($('[name="footer-subscribe-email"]').val());
    if ($('[name="footer-subscribe-email"]').val()) {
      $('[name="footer-subscribe-email"]').attr('disabled', true);
      $('[name="footer-subscribe-button"]').val("Sending...")
        .attr("disabled", true);
      erpnext.subscribe_to_newsletter({
        email: $('[name="footer-subscribe-email"]').val(),
        callback: function (r) {
          if (!r.exc) {
            $('[name="footer-subscribe-button"]').val(__("Added"))
              .attr("disabled", true);
          } else {
            $('[name="footer-subscribe-button"]').val(__("Error: Not a valid id?"))
              .addClass("btn-danger").attr("disabled", false);
              $('[name="footer-subscribe-email"]').val("").attr('disabled', false);
          }
        }
      });
    }
    else {
      $('form.subscribeForm.validation').html(__('Wrong Input')).show('blind');
    }
    return false;
  });

  $('form.php-email-form').submit(function(e) {
    e.preventDefault();
    
    var f = $(this).find('.form-group'),
      ferror = false,
      emailExp = /^[^\s()<>@,;:\/]+@\w[\w\.-]+\.[a-z]{2,}$/i;

    f.children('input').each(function() { // run all inputs
     
      var i = $(this); // current input
      var rule = i.attr('data-rule');

      if (rule !== undefined) {
        var ierror = false; // error flag for current input
        var pos = rule.indexOf(':', 0);
        if (pos >= 0) {
          var exp = rule.substr(pos + 1, rule.length);
          rule = rule.substr(0, pos);
        } else {
          rule = rule.substr(pos + 1, rule.length);
        }

        switch (rule) {
          case 'required':
            if (i.val() === '') {
              ferror = ierror = true;
            }
            break;

          case 'minlen':
            if (i.val().length < parseInt(exp)) {
              ferror = ierror = true;
            }
            break;

          case 'email':
            if (!emailExp.test(i.val())) {
              ferror = ierror = true;
            }
            break;

          case 'checked':
            if (! i.is(':checked')) {
              ferror = ierror = true;
            }
            break;

          case 'regexp':
            exp = new RegExp(exp);
            if (!exp.test(i.val())) {
              ferror = ierror = true;
            }
            break;
        }
        i.next('.validate').html((ierror ? (i.attr('data-msg') !== undefined ? i.attr('data-msg') : 'wrong Input') : '')).show('blind');
      }
    });
    f.children('textarea').each(function() { // run all inputs

      var i = $(this); // current input
      var rule = i.attr('data-rule');

      if (rule !== undefined) {
        var ierror = false; // error flag for current input
        var pos = rule.indexOf(':', 0);
        if (pos >= 0) {
          var exp = rule.substr(pos + 1, rule.length);
          rule = rule.substr(0, pos);
        } else {
          rule = rule.substr(pos + 1, rule.length);
        }

        switch (rule) {
          case 'required':
            if (i.val() === '') {
              ferror = ierror = true;
            }
            break;

          case 'minlen':
            if (i.val().length < parseInt(exp)) {
              ferror = ierror = true;
            }
            break;
        }
        i.next('.validate').html((ierror ? (i.attr('data-msg') != undefined ? i.attr('data-msg') : 'wrong Input') : '')).show('blind');
      }
    });
    if (ferror) return false;

    var this_form = $(this);
    /*var action = $(this).attr('action');

    if( ! action ) {
      this_form.find('.loading').slideUp();
      this_form.find('.error-message').slideDown().html('The form action property is not set!');
      return false;
    }*/
    
    this_form.find('.sent-message').slideUp();
    this_form.find('.error-message').slideUp();
    this_form.find('.loading').slideDown();

    if ( $(this).data('recaptcha-site-key') ) {
      var recaptcha_site_key = $(this).data('recaptcha-site-key');
      grecaptcha.ready(function() {
        grecaptcha.execute(recaptcha_site_key, {action: 'php_email_form_submit'}).then(function(token) {
          php_email_form_submit(this_form,this_form.serialize() + '&recaptcha-response=' + token);
        });
      });
    } else {
      php_email_form_submit(this_form,this_form.serialize());
    }
    
    return true;
  });

  function php_email_form_submit(this_form, data) {
    frappe.send_message({
      subject: $('[name="subject"]').val(),
      sender: $('[name="email"]').val(),
      message: $('[name="message"]').val(),
      callback: function (r) {
        if (r.message === "okay") {
          this_form.find('.loading').slideUp();
          this_form.find('.sent-message').slideDown();
          this_form.find("input:not(input[type=submit]), textarea").val('');
        } else {
          this_form.find('.loading').slideUp();
          if(!msg) {
            msg = 'Form submission failed and no error message returned from: ' + action + '<br>';
          }
          this_form.find('.error-message').slideDown().html(msg);
          console.log(r.exc);
        }
      }
    }, this);    
  }

})(jQuery);
