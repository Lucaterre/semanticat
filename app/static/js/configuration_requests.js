/*

Script for Semantic@ configuration page.

Author : Lucas Terriel
Date : 06/01/2021 
*/

const ProjectID                    = $('.project_id').attr('id').split('_')[1];
const ListModels                   = $('#model_type_list');
const ListSpacyLanguages           = $('#langs_spacy_available');
const RecommenderSettingsContainer = $('#ner-recommenders-settings');

const LanguageModelField            = $('#recommender-language-field');
const TypeNerModelField             = $('#recommender-model-name-field');
const ListTagSetField               = "";
let PerformanceModelScore;

var flashMessage = function (data) {
    /*
    Create a flash message when Ajax request is send.
    */
    console.log(data);
    html = '';
    html += '<div class="alert alert-' + data['type'] + '"><a href="#" class="close" data-dismiss="alert">&times;</a><b>' + data['message'] + '</b></div>';
    return html;
};

function get_list_model(){
    $.ajax({
    type:'GET',
    url:'/models',
    success: function(data){
        let list_models = data['available_models'];
        for (let i in list_models){
            ListModels.append("<option value="+list_models[i]+">"+list_models[i]+"</option>");
        }
    }
})
}

function get_languages_spacy(){
    $.ajax({
        type:'GET',
        url:'/spaCy_languages',
        success : function(data){
            let spacy_languages = data['available_langs'];
            for (let i in spacy_languages){
                ListSpacyLanguages.append("<option value="+spacy_languages[i]+">"+spacy_languages[i]+"</option>");
            }
        }
    })
}

function get_actual_recommender(){
    $.ajax({
    type:'GET',
    url:'/actual_configuration_recommender/'+ProjectID,
    success: function (data) {
        LanguageModelField.text(data.language);
        TypeNerModelField.text(data.model_type);
        PerformanceModelScore = data.ner_performance;
        createPlotModelPerformance(PerformanceModelScore);
        let tagset = []
        try{
            tagset = data.model_tag_set.split(',');
        }catch(e){}
        for (let i in tagset){
        $('#actual-mapping-tagset').append("<li class="+tagset[i]+">"+tagset[i]+"</li>");
       }
    }
});

}

function get_actual_mapping(){
    $.ajax({
   type:'GET',
   url:'/actual_mapping/'+ProjectID,
   success:function (data){
       let mapping = data['available_tags'];
       for (let i in mapping){
        $('#actual-mapping-tagset').append("<li class="+mapping[i]+">"+mapping[i]+"</li>");
       }
   }
});
}


get_list_model();
get_actual_recommender();
get_languages_spacy();
//get_actual_mapping();


$('#apply-recommender-anyway').click(function () {
    sendNerRecommenderConfiguration();
})

function openCloseSettingsContainer(element, idContainer, idBtnConfirm) {
    if(element.checked){
        $(idContainer).css('display', 'inline');
        $(idBtnConfirm).css('display', 'inline');
    }
    else{
        $(idContainer).css('display', 'None');
        $(idBtnConfirm).css('display', 'None');
    }
}

function sendNerRecommenderConfiguration(){
    let inputs     = $('#ner-recommender-form').serializeArray();
    let language   = inputs[0].value.toString();
    let model_type = inputs[1].value.toString();
    let data       = {'language':language,
                      'model_type':model_type};
    console.log(data)
    if (inputs.length > 0) {

        $.ajax({
            async:false,
            type:'POST',
            url:'/new_ner_recommender_configuration/'+ProjectID,
            data:JSON.stringify(data),
            contentType: 'application/json; charset=utf-8',
            success: function () {
                $('#state-ner-recommender').css("color","#28b463").removeClass("fa-times").addClass("fa-check");
                LanguageModelField.text(language);
                TypeNerModelField.text(model_type);
                window.location.reload();
            },
            error: function (){
                $('#state-ner-recommender').css("color","#c0392b").removeClass("fa-check").addClass("fa-times");
            }
        });
    }


}

$("input.check-language").on('click', function() {
    // in the handler, 'this' refers to the box clicked on
    var $box = $(this);
    if ($box.is(":checked")) {
        // the name of the box is retrieved using the .attr() method
        // as it is assumed and expected to be immutable
        var group = "input:checkbox[name='" + $box.attr("name") + "']";
        // the checked state of the group/box on the other hand will change
        // and the current value is retrieved using .prop() method
        $(group).prop("checked", false);
        $box.prop("checked", true);
    } else {
        $box.prop("checked", false);
    }
});


function detectChange(element) {

    $(element).on('focus', function () {
        const freezeValue = $(this).val();
        $(element).on('input', function () {
            var currentValue = $(this).val();
            var row = $(this).closest("tr");
            var mappingId = row.context.id.split("_")[1]
            if (freezeValue == currentValue) {
                $('#saveModificationTable_' + mappingId).css("background-color", "green");
                $('#saveModificationTable_' + mappingId).css("border-color", "green");
            } else {
                $('#saveModificationTable_' + mappingId).css("background-color", "gray");
                $('#saveModificationTable_' + mappingId).css("border-color", "gray");
            }
        })
    });
}

detectChange('input[name="NerPrefLabel"]')
detectChange('input[name="tableColor"]')

// Ajax requests

function remove_pair_ner_label(item) {
    var mappingId = $(item).val();
    var mappingIDStr = mappingId.toString();
    $.ajax({
        type: 'POST',
        url: "/remove_pair_ner_label/"+ProjectID,
        data: { mapping_id: mappingId },
        dataType: "text",
        success: function (data) {
            $('#flash_javascript').append(flashMessage(JSON.parse(data)));
            $("#mapping_" + mappingIDStr).remove();
            document.location.reload();
        }
    });
};

function save_pair_ner_label(item) {
    var mappingId = $(item).val();
    var mappingIDStr = mappingId.toString();
    var nerLabel = $("#nerLabel_" + mappingIDStr).val();
    var prefNerLabel = $("#prefNerLabel_" + mappingIDStr).val();
    var color = $("#color_" + mappingIDStr).val();

    $.ajax({
        type: 'POST',
        url: '/save_pair_ner_label',
        data: {
            mapping_id: mappingId,
            nerLabel: nerLabel,
            prefNerLabel: prefNerLabel,
            color: color
        },
        dataType: "text",
        success: function (data) {
            $('#saveModificationTable_' + mappingIDStr).css("background-color", "green");
            $('#saveModificationTable_' + mappingIDStr).css("border-color", "green");
            $('#flash_javascript').append(flashMessage(JSON.parse(data)));
        }
    });

};

function new_pair_ner_label(project_id) {
    var projectID = project_id;
    var newLabel = $('#NewNerLabel').val();
    var prefNewLabel = $('#NewPrefNerLabel').val();
    var newColor = $('#NewColorPair').val();

    // Check if input values are empty
    if (newLabel.length == 0) {
        $('#invalidFeedbackNerLabel').text("Value is empty");
        $('#NewNerLabel').addClass('is-invalid');
    }

    if (prefNewLabel.length == 0) {
        $('#invalidFeedbackPrefNerLabel').text("Value is empty");
        $('#NewPrefNerLabel').addClass('is-invalid')
    }

    if (prefNewLabel.length != 0 && newLabel.length != 0) {
        $('#NewNerLabel').removeClass('is-invalid')
        $('#NewPrefNerLabel').removeClass('is-invalid')
        $.ajax({
            type: 'POST',
            url: '/new_pair_ner_label',
            data: {
                project_id: projectID,
                nerLabel: newLabel,
                prefNerLabel: prefNewLabel,
                color: newColor
            },
            dataType: "text",
            success: function (data) {
                document.location.reload();
            },
            error: function (data) {
                var json = JSON.parse(data.responseText);
                if (json.message == "invalid") {
                    $('#invalidFeedbackNerLabel').text("Label is invalid (Check Ner tagset)");
                    $('#NewNerLabel').addClass('is-invalid');
                } else if (json.message == "duplicate") {
                    $('#invalidFeedbackNerLabel').text("Label already exist in Mapping Scope");
                    $('#NewNerLabel').addClass('is-invalid');
                };
            }
        });
    };
};

function createPlotModelPerformance (perfScore){

         var data = [

            {

                domain: { x: [0, 1], y: [0, 1] },

                value: perfScore,

                number: { suffix: "%" },

                title: { text: "NER performance (F-score)" },

                type: "indicator",

                mode: "gauge+number",

                gauge: {

                    axis: { range: [null, 100] }

                }

            }];


        var layout = { autosize: true,
            paper_bgcolor:"rgb(255, 255, 255)"};

        $(window).on('resize', function(){
            Plotly.relayout('ner_perf_gauge', {
                'xaxis.range': "auto",
                'yaxis.range': "auto"
            });
        });

        Plotly.newPlot('ner_perf_gauge', data, layout, {displaylogo: false, displayModeBar: false});



    }