$(document).ready(function(){

    $('[data-toggle="popover"]').popover();

    $.fn.scrollView = function () {
        return this.each(function () {
            $('html, body').animate({
                scrollTop: $(this).offset().top - 50
            }, 1000);
        });
    }

    var colors = ['#a3a375', '#7a1f5c', '#006666', '#2d8659', '#2d8659'];

    function render(frame, id){
        // show sentence with fancy boxes indicating parts of construction
        var head_id = frame[0];
        var sent = '';
        var quotcount = 0;
        var nospace = false;
        for (var i = 0; i < frame[1].length; i++) {
            var token = frame[1][i];
            var lemma = token[2];

            if (token[3] == 'PUNC' || token[3] == 'SENT') { // no fancy stuff for punctuation
                if (lemma == '-') {
                    lemma = '—';
                }
                if (lemma == '"') {
                    quotcount++;
                }
                if (lemma == '.' || lemma == ',' || lemma == '!' || lemma == '?' || lemma == ':' || lemma == ';' || lemma == ')' || lemma == '»' || lemma == '…' || (lemma == '"' && quotcount % 2 == 0) || nospace) { // punctuation that does not require spaces before it
                    sent = sent + lemma;
                } else {
                    sent = sent + ' ' + lemma;
                }
            } else {
                var poptitle = token[2];
                var popcontent = token[3];
                if (token[5] != '_') {
                    popcontent = popcontent + ' ' + token[5];
                }
                var popline = "<a href='#" + id + "' data-toggle='popover' data-trigger='focus' data-placement='bottom' data-html='true'" +
                              "title='" + poptitle + "' data-content='" + popcontent
                var space = (nospace || token[1] == '%') ? '' : ' '; // here was a quot or a parenthesis
                if (token[8] != 0) { // fancy boxes and popovers for frame parts
                    if (token[8] != 1) {
                        if (token[9] != '_') {
                            popline = popline + ' | ' + token[9]; 
                        } else {
                            popline = popline + ' | ' + token[7];
                        }
                    }
                        sent = sent + space + "<span class='label' style='background-color:" + colors[token[8]] + "'>" + popline +
                               "' class='boxedlemma'>" + token[1] + "</a></span>";
                } else { // only popovers for not frame parts
                    sent = sent + space + popline + "' class='plainlemma'>" + token[1] + "</a>";
                }
            }
            nospace = (lemma == '(' || lemma == '«' || (lemma == '"' && quotcount % 2 == 1));
        }
        return sent;
    }

    function show_extracted(data){
        if (data.error != 'NoError') {
            if (data.error == 'FileNotFoundError') {
                $("#alerts").append('<div class="alert alert-danger"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><strong>No such word in the index. Try another one please.</strong></div>');
            } else {
                if (data.error == 'NoExtract') {
                    $("#alerts").append('<div class="alert alert-info"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><strong>Found nothing. Try other extraction options please.</strong></div>');
                } else {
                    if (data.error == 'TooMany') {
                        $("#alerts").append('<div class="alert alert-info"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><strong>Found too many constructions to display. Try to refine extraction options please.</strong></div>');
                    }
                }
            }
        } else {
            $("#extracted").text("");
            var i = 0;
            $.each(data.classes, function(){
                var constr = this == '' ? 'empty' : this;
                var text = constr + "<span class='badge'>" + data.frames[this].length + "</span>";
                $("<div class='panel panel-default col-md-12' id='class" + i + "'></div>")
                    .html("<div class='panel-heading'><h4 class='panel-title'><a data-toggle='collapse' href='#collapse" + i + "'>" + text + "</a></h4></div>")
                    .appendTo($("#extracted"));
                $("<div id='collapse" + i + "' class='panel-collapse collapse'></div>")
                    .html("<ul class='list-group' id='ul" + i + "'></ul>")
                    .appendTo($('#class' + i));
                $.each(data.frames[this], function(){
                    $("ul#ul" + i).append("<li class='list-group-item'>" + render(this, "#class" + i) + "</li>");
                });
                i++;
            });
            $('[data-toggle="popover"]').popover();

            // draw a graph
            sigma.parsers.json(
            data.json, 
            {
               container: 'container',
               settings: 
                 {
                    defaultNodeColor: '#006666',
                    labelThreshold: 0,
                    sideMargin: 5,
                  },
            },
            function(s) {
                s.bind('clickNode', function(e) {
                    //console.log('Something happened at ' + e.data.node.id);
                    var classId = '#class' + e.data.node.id.substring(1);
                    $(classId).scrollView();
                    var collapseId = '#collapse' + e.data.node.id.substring(1);
                    $(collapseId).collapse('show');
                });
            });
            $('#container').show();
        }
        $('#loading-indicator').hide();
    }

    function extract(){
        // get options and ask for extraction
        $.getJSON(
            json_extracted,
            {lemma:$('#lemma').val(),
             pos:$('input[name=pos]:checked', '#query').val(),
             corpus:$('input[name=corpus]:checked', '#query').val(),
             usepos:$('input[name=usepos]', '#query').is(":checked"),
             usecase:$('input[name=case]', '#query').is(":checked"),
             useanim:$('input[name=animacy]', '#query').is(":checked"),
             splice:$('input[name=splice]', '#query').is(":checked"),
             strip:$('input[name=strip]', '#query').is(":checked"),
             threshold:$('#threshold').val(),
             posfeats:$('#posfeats').val(),
             negfeats:$('#negfeats').val(),
             posrels:$('#posrels').val(),
             negrels:$('#negrels').val(),
             prnegrels:$('#prnegrels').val()
            },
            show_extracted
        )
    }

    $("#extractbutton").click(function(){
        event.preventDefault();
        $("#alerts").html("");
        var lemma = $('#lemma').val();
        if (lemma == '') {
            // no lemma entered, can't extract
            $("#alerts").append('<div class="alert alert-danger"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><strong>Please enter lemma!</strong></div>');
        } else {
            var threshold = +($('#threshold').val());
            if (isNaN(threshold) || threshold < 0 || $('#threshold').val() == '') {
                // somehow min threshold is not a number
                $("#alerts").append('<div class="alert alert-danger"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><strong>Please enter positive integer value for minimal frequency!</strong></div>');
            } else {
                  if ($('input[name=corpus]:checked', '#query').val() == 'post') {
                      $("#alerts").append('<div class="alert alert-danger"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><strong>Sorry, Russian National Corpus is temporarily unavailable due to the host regulations.</strong></div>');
                  } else {
                        // everything ok
                        $('#loading-indicator').show();
                        $('#container').hide();
                        $('#container').html('');
                        $('#extracted').text('');
                        extract();
                  }
            }
        }
    });
});
