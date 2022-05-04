const BatchProgressBarContainer = $('.progress-batch');
const BatchProgessBar           = $('#progressbar-component-progress-batch');
const BatchProgressBarLabel     = $('.progress-bar-label-batch');
const WarningNerProcessBtn      = $('.modal-warning-launch-ner-process');
const ProjectID                 = $('.global_project_id').attr('id');
const globalStatsNerContainer   = $('#chart')

const SuccessStyle = {'border-color':'#2cb23e', 'background-color':'#2cb23e'};
const ErrorStyle   = {'border-color':'#d62728', 'background-color':'#d62728'};
let counter = 0, percentage = 0, totalDocuments = 0;
let documentsID;


// function to increment progress bar for batch processing (parsing, ner)
function IncrementGenericProgressBar (counterStatus, type, progressBarActive, progressBarActiveLabel) {
    let progressTypeClass;
    if(type === "success"){
        progressTypeClass = "bg-success";
    }
    else{
        progressTypeClass = "bg-danger";
    }
    progressBarActive.addClass(progressTypeClass);
    progressBarActive.css('width', counterStatus + '%').attr('aria-valuenow', counterStatus);
    progressBarActiveLabel.text(counterStatus + '%');
}

// function to diasable buttons during process
// TODO : Keep Shuthdown + Cancel + flash message btns alive !
function disableUserActions(action){
    $("button").prop('disabled', action);
    $("a").prop('disabled', action);
}

function addSpinnerBtn(btn, spinner_id){
    $(btn).html(
        `<i id="${spinner_id}" class="fa fa-spinner fa-spin"></i> Loading`
    );
}

function GetPercentage(current, total){
    return Math.floor(current / total * 100);
}

function initProcess(btn, identifier){
    disableUserActions(true);
    addSpinnerBtn(btn, identifier);
}

// function to apply NER
function run_ner(project_id, document_id, rewrite=0){
    let button_ner = $("[name=all_parse_"+document_id+"]");
    initProcess(button_ner, "spinner_" + document_id);
    //disableUserActions(true);
    //addSpinnerBtn(button_ner, "spinner_" + document_id);
    $(".progress-" + document_id).css('display', '');
    // Listen process to plot in progress bar
    let ProgressBarNerComponent = $('#progressbar-component-' + document_id);
    let ProgressBarNerLabel     = $('.progress-bar-label-' + document_id);
    let source = new EventSource("/progress_ner/PROJECT=" + project_id + "/DOCUMENT=" + document_id + "/" + rewrite);
    source.onmessage = function (event) {
        IncrementGenericProgressBar(event.data, 'success', ProgressBarNerComponent, ProgressBarNerLabel);
        // Exit when the process is 100%
        if (parseInt(event.data) === 100) {
            source.close()
            document.location.reload();

        }
    }
}

// function to parse on documents
function run_parse(project_id, doc_id, reload=true) {
    let button_parse = $("[name=all_parse_"+doc_id+"]");
    let status = "";
    initProcess(button_parse, "spinner_" + doc_id);
    //disableUserActions(true);
    //addSpinnerBtn(button_parse, "spinner_" + doc_id);
    $.ajax({
        async:false,
        type: 'GET',
        url: '/progress_parse/PROJECT='+ project_id + '/DOCUMENT=' + doc_id,

        success: function (data) {
            if (data.status === "success"){
                if(reload){
                    document.location.reload();
                }
                else{
                    $('#spinner_' + id).remove();
                    button_parse.html("Process completed").css(SuccessStyle);
                    status = "success";
                }
            }
        },
        error : function(){
            $('#spinner_' + doc_id).remove();
            button_parse.html("Parsing Error. Check the XML schema and import document again.").css(ErrorStyle);
            status = "error"
            if(reload){
             window.location.reload();
            }
        }
    });
    return status
}

function run_batch_parsing(element, project_id, documentsID){
    totalDocuments = documentsID.length;
    initProcess(element, "spinner");
    // disableUserActions(true);
    // addSpinnerBtn(element, "spinner");
    BatchProgressBarContainer.css('display', '');
    for (id of documentsID.values()){
        counter++;
        let response = run_parse(project_id, id, false);
        if (response === "success") {
            IncrementGenericProgressBar(GetPercentage(counter, totalDocuments), "success", BatchProgessBar, BatchProgressBarLabel);
        }
        else {
            IncrementGenericProgressBar(GetPercentage(counter, totalDocuments), "error", BatchProgessBar, BatchProgressBarLabel);
        }
    }
    document.location.reload();
}

function run_batch_ner(element, project_id, documentsID){
    totalDocuments = documentsID.length;
    initProcess(element, "spinner");
    BatchProgressBarContainer.css('display', '');
    for (id of documentsID.values()){
        let currentNerDoc = $("[name=all_ner_"+id+"]");
        addSpinnerBtn(currentNerDoc, "spinner_ner_"+id);
        $.ajax({
            async:false,
            type:'GET',
            url: "/progress_ner/PROJECT=" + project_id + "/DOCUMENT=" + id + "/" + 0,
            success: function (data) {
                if (data.status === 400){
                    counter++;
                IncrementGenericProgressBar(GetPercentage(counter, totalDocuments), "error", BatchProgessBar, BatchProgressBarLabel);
                $('#spinner_ner_' + id).remove();
                currentNerDoc.html("NER failed").css(ErrorStyle);

                }else{
                 counter++;
                IncrementGenericProgressBar(GetPercentage(counter, totalDocuments), "success", BatchProgessBar, BatchProgressBarLabel);
                $('#spinner_ner_' + id).remove();
                currentNerDoc.html("NER completed").css(SuccessStyle);
                }
            },
            error: function () {
                counter++;
                IncrementGenericProgressBar(GetPercentage(counter, totalDocuments), "error", BatchProgessBar, BatchProgressBarLabel);
                $('#spinner_ner_' + id).remove();
                currentNerDoc.html("NER failed").css(ErrorStyle);
            }
        })
    }
    document.location.reload();
}


function loading_export(project_id, document_id){
    $(".modal").modal('hide');
    // addSpinnerBtn($('#export-doc-'+document_id), "spinner-export-"+document_id);
}


WarningNerProcessBtn.click(function () {
    $(".modal").modal('hide');
});

// Display a chart containing proportion of entities in project
function plotStaticsNerProject(values, labels){
    let data = [{

            values: values,
            labels: labels,
            hole: .4,
            type: 'pie',
            textposition: 'inside',
            automargin: true

        }];
        let layout = {
            title: 'NER Entities report',
            autosize: true // set autosize to rescale
        };
        $(window).on('resize', function(){
            Plotly.relayout('chart', {
                'xaxis.range': "auto",
                'yaxis.range': "auto"
            });
        });
        Plotly.newPlot('chart', data, layout, {displaylogo: false});
}

$.ajax({
    type:"GET",
    url:'/get_ner_statistics_project/'+ProjectID,
    success:function (data) {
        if (data.values.length !== 0){
            globalStatsNerContainer.css('display', 'block');
            plotStaticsNerProject(data.values, data.labels);
        }
        else{
            globalStatsNerContainer.css('display', 'None')
        }
    }
})
