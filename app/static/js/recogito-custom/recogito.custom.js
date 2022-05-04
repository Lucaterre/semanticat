(function() {
    // params templates
    const project_id = document.querySelector('.project_id').id.split('_')[1]
    const document_id = document.querySelector('.document_id').id.split('_')[1]
    try{
        var page_id     = document.querySelector('#actual_page').textContent
    }catch (e) {
        var page_id     = 0
    }


    // Init annotation DOM container
    var textContent            = document.querySelector('#text');
    textContent.hidden = true;
    // sometimes we can't access directly to the stylesheet
    const textPre                = window.getComputedStyle(document.getElementById('text'), null);
    // Init constants
    const totalAnnotationsSpan   = document.querySelector('#total-annotation');
    const mentionCountBadges     = document.querySelectorAll('.badge');
    // const ResetAllDemoAnnotsBtn  = document.querySelector("#added-all-annotations");
    const RemoveAllAnnotsBtn     = document.querySelector("#remove-all-annotations");
    const btnZoomIn              = document.querySelector("#zoomIn");
    const btnZoomOut             = document.querySelector("#zoomOut");
    const searchInput            = document.querySelector("#search-input");
    const clearInput             = document.querySelector("#clear-input-text");
    const annotationsArea        = document.querySelector("#number-annotations");
    const allRemoveButtonsInList = document.querySelectorAll('.btn-remove');
    const spinnerLoadDoc         = document.querySelector('#spinner-load');
    const loadJsonAnnotationsBtn = document.querySelector('#import_json');
    const spinnerLoadRemoveMeta  = document.querySelector('#spinner-meta-annotation-loading');



    // Attach listeners functions to elements
    searchInput.onkeyup = searchInput.onfocus = searchInput.onblur = clearInput.onclick = textContent.onclick = queryMentions;
    btnZoomIn.onclick = btnZoomOut.onclick  = zoomText;
    annotationsArea.onclick = annotationsArea.onbind = listHandler;
    textContent.onmouseover = textContent.onmouseout  =  spanHandler;
    RemoveAllAnnotsBtn.onclick = RemoveAllAnnotations;
    // ResetAllDemoAnnotsBtn.onclick = reloadDemoAnnotations;

    // Init fetch and send functions :
    // function to send data to backend
    function sendData(data, url){
        let r = fetch(url, {
            method  :"POST",
            headers : new Headers({"Content-Type" : "application/json"}),
            body    : JSON.stringify(data)
        })
        return r
    }

    // Get user mapping (label/color) from user config (db)
    const fetchMapping = fetch("/mapping/"+project_id)
        .then((response) => response.json())
        .then((res) => {
            return res;
        });

    // Get labels statitics (db)
    const fetchStatsLabel = fetch("/get_statitics/"+document_id)
        .then((response) => response.json())
        .then((res) => {
            return res;
        });

    // Init async utils functions :
    // Get numbers of entities in badges
    const addLabelsStatsInfo = async () => {
        await fetchStatsLabel.then((stats) => {
            for (const [label, value] of Object.entries(stats)) {
                document.querySelector('#entityLabelCount-' + label).textContent = value.toString();
            }
        });
    };
    // Add a specific colors mapping for labels
    const stylizeMapping = async () => {
        let style       = document.createElement('style');
        style.setAttribute('type', 'text/css');
        style.innerHTML = "";
        await fetchMapping.then((mapping) =>{
            for (const [label, desc] of Object.entries(mapping)) {
                style.innerHTML += "."+label+"{background-color:"+desc[0]+";}";
            }
            document.querySelectorAll('head')[0].appendChild(style);
        });
    };

    /*
    * Custom Recogito Widgets
    *
    * 1. colorLabelSelectorWidget : Dynamics color highlight label assignation (formater) with tagging property ;
    * 2. mentionLabelWidget       : Give current mention and label information to the user in infobox.
    */
    const colorLabelSelectorWidget =  function (args) {
        // Find a current color setting in the annotation, if any
        let currentColorBody = args.annotation ?
            args.annotation.body.find(function (b) {
                return b.purpose  === 'highlighting';
            }) : null;
        // find current p selection (sentences if exist)
        let currentNodeTextSelection = window.getSelection().anchorNode ;
        let overlap = false;
        try {
            if (currentNodeTextSelection.nodeName === "SPAN" || currentNodeTextSelection.nextSibling.nodeName === "SPAN" && currentNodeTextSelection.parentElement.nodeName !== "SPAN") {
                overlap = true;
            }
        }
        catch (e) {}

        let sentenceID = 0;
        try{
            if(currentNodeTextSelection.nodeName === "P"){
                sentenceID = currentNodeTextSelection.id;
            }
        }catch(e){}

        // Keep the value in a variable
        let currentColorValue = currentColorBody ? currentColorBody.value : null;
        // Triggers callbacks on user action (here combined highlight & tagging actions)
        const addTag = function (evt) {
            if (currentColorBody) {
                args.onUpdateBody(currentColorBody, {
                    type: 'TextualBody',
                    purpose: 'highlighting',
                    value: evt.target.dataset.tag,
                    sentenceID : sentenceID
                });

            } else {
                args.onAppendBody({
                    type: 'TextualBody',
                    purpose: 'highlighting',
                    value: evt.target.dataset.tag,
                    sentenceID : sentenceID
                });
            }
        }
        const addLabel = function (evt) {
            if (currentColorBody) {
                args.onUpdateBody(currentColorBody, {
                    type: 'TextualBody',
                    purpose: 'tagging',
                    value: evt.target.dataset.tag,
                    sentenceID : sentenceID
                });

            } else {
                args.onAppendBody({
                    type: 'TextualBody',
                    purpose: 'tagging',
                    value: evt.target.dataset.tag,
                    sentenceID : sentenceID
                });
            }
        }
        // This part renders the UI elements
        let container = document.createElement('div');
        if(overlap === false) {
            const createButton = function (value) {
                let button = document.createElement('button');
                if (value === currentColorValue){
                    button.className = 'selected';
                }
                button.className             = value;
                button.textContent           = value;
                button.dataset.tag           = value;
                button.style.backgroundColor = value;
                button.classList.add("btn");
                button.addEventListener('click', addTag);
                button.addEventListener('click', addLabel);
                return button;
            }
            let title     = document.createElement('h3');
            let line      = document.createElement('hr');

            // add attribute / content
            container.className = 'colorselector-widget';
            title.textContent = "Labels"
            // add children to DOM
            container.appendChild(title);
            container.appendChild(line);
            // This part render label button with specified mapping
            const stylizeBox = async () => {
                const mapping = await fetchMapping;
                for (let key in mapping) {
                    let button = createButton(key);
                    container.appendChild(button);
                }
            };
            stylizeBox().then();
        }
        else{
            container.innerHTML = "<p style='color: red'>Annotations overlap detected</p>";
        }
        return container;

    }
    // style formatter for applying color on labels
    const ColorFormatter = function (annotation) {
        let highlightBody = annotation.body.find(function (b) {
            return b.purpose === 'highlighting';
        });
        if (highlightBody) {
            return highlightBody.value;
        }

    }

    const MentionLabelWidget = function(args){
        let actualMention     = args.annotation.underlying.target.selector[0].exact
        let title             = document.createElement('h3');
        let line              = document.createElement('hr');
        let container         = document.createElement('div');
        let labelMentionInput = document.createElement('label')
        let form              = document.createElement('form');
        let inputMention      = document.createElement('input');
        let labelLabelInput   = document.createElement('label')
        let inputLabel        = document.createElement('input');
        let br                = document.createElement('br');
        //title.textContent = " Description";
        //title.className = "preserve-whitespace";
        labelMentionInput.setAttribute("for", "mention");
        labelMentionInput.textContent = " Mention";
        labelMentionInput.className = "preserve-whitespace";
        form.className = "form-group";
        inputMention.setAttribute('disabled', 'true');
        inputMention.setAttribute('size', '30');
        inputMention.id = "mention";
        inputMention.name = "mention";
        inputMention.value = actualMention;
        inputMention.className = "form-control";
        labelLabelInput.setAttribute("for", "label");
        labelLabelInput.textContent = " Label";
        labelLabelInput.className = "preserve-whitespace";
        inputLabel.setAttribute('disabled', 'true');
        inputLabel.setAttribute('size', '15');
        inputLabel.id = "label";
        inputLabel.name = "label";
        inputLabel.className = "form-control";
        try{
            inputLabel.value = args.annotation.underlying.body[0].value;
        }catch{
            inputLabel.value = "";
        }
        form.appendChild(labelMentionInput);
        form.appendChild(inputMention);
        form.appendChild(br);
        form.appendChild(labelLabelInput);
        form.appendChild(inputLabel);
        //container.appendChild(title);
        //container.appendChild(line);
        container.appendChild(form);
        return container;
    };

    /*
    *    BASE
    */
    // Init Recogito JS annotation object

    const Recogito = window.Recogito;
    const r = Recogito.init({
        content: textContent,
        widgets: [
            MentionLabelWidget, colorLabelSelectorWidget
        ],
        formatter: ColorFormatter,
        // Use option "pre" meanly the text comes is pre-formated
        // (important for the offsets)
        mode:"pre"

    });

    // Load text
    //addText().then();
    // loaded the previous annotations (from db)
    r.loadAnnotations("/annotations/"+document_id+"/"+page_id).then(function () {
        spinnerLoadDoc.hidden = true;
        textContent.hidden = false;
    });
    const jsonInput = document.querySelector('#json-input');
    loadJsonAnnotationsBtn.addEventListener("click", function (event){
        jsonInput.click();
    })

    jsonInput.onchange = function(event) {
        let fileList = jsonInput.files;
        let reader = new FileReader();
        reader.onload = function () {
            let json = JSON.parse(reader.result);
            sendData(json, '/load_annotations_from_json/'+project_id+'/'+document_id).then(function () {
                document.location.reload();
            });
        }
        reader.readAsText(fileList[0])

    }

    //document.getElementById('json-input').click();

    // Apply init functions and set values elements on page reload
    searchInput.value = "";
    addLabelsStatsInfo().then();
    stylizeMapping().then();

    // Specific handlers for recogito : https://github.com/recogito/recogito-js/wiki/API-Reference
    r.on('createAnnotation', function (annotation) {
        let data = prepareData(annotation);
        sendData(data, "/new_annotation");
        updateListControl(annotation, "more");
    });

    r.on('deleteAnnotation', function (annotation) {
        let data = prepareData(annotation);
        sendData(data, "/delete_annotation");
        updateListControl(annotation, "less");
    });

    r.on('updateAnnotation', function (annotation, previous) {
        // get previous annotation informations here
        let data = prepareData(previous);
        // get new label to update annotation
        let newLabel = {updatedLabel : annotation.body[0].value};
        // concatenate previous and new data dict
        sendData(Object.assign({}, data, newLabel), "/update_annotation");

        // updateListControl(annotation, "more");
        updateListControl(previous, "less");
        updateListControl(annotation, "more");
    });

    /*
    * Utils functions
    */

    // Count total annotations and set value in general badge
    const sumAnnots = (totalAnnotationsCounter) => {
        let count = 0;
        mentionCountBadges.forEach(function (badge){
            count += parseInt(badge.innerHTML);
        });
        totalAnnotationsCounter.textContent = count;
    }

    //Remove all annotations
    const addRemoveEventOnAll = (allRemoveBtnList)=> {
        allRemoveBtnList.forEach(function (btn) {
            btn.onclick = RemoveAllItems;
        });
    }

    // Init functions on page reload
    sumAnnots(totalAnnotationsSpan);
    addRemoveEventOnAll(allRemoveButtonsInList);

    // Reload demo annotations
    function reloadDemoAnnotations(){
        r.clearAnnotations();
        resetListsMentions();
        r.loadAnnotations("/reload_demo_annotations").then(function () {
            let allAnnotations = r.getAnnotations();
            for (let annotation in allAnnotations){
                updateListControl(allAnnotations[annotation], 'more');
            }
        })
    }

    // Data wrapper
    function prepareData(annotation){
        let mention = annotation.target.selector[0].exact;
        let start   = annotation.target.selector[1].start;
        let end     = annotation.target.selector[1].end;
        let label   = annotation.body[0].value;
        let sentenceID = annotation.body[0].sentenceID;
        return {
            id          : annotation.id,
            mention     : mention,
            label       : label,
            start       : start,
            end         : end,
            documentID  : document_id,
            projectID   : project_id,
            sentenceID  : sentenceID
        }
    }

    // Updated list information on recogito events
    function updateListControl(annotation, type){
        let mention = annotation.target.selector[0].exact;
        let label   = annotation.body[0].value;
        let actualCount = parseInt(document.getElementById("entityLabelCount-"+label).textContent);
        if(type === "more"){
            let labelList = document.getElementById("list-"+label)
            try{
                let itemListBadge   = document.getElementById("list-badge-"+label+"-"+mention);
                let actualBadgeCount = parseInt(itemListBadge.textContent);
                itemListBadge.textContent = actualBadgeCount + 1;
            }catch {
                // add new list item
                let newListItemMention = document.createElement("li");
                let newListBadge = document.createElement("span");
                let newRemoveBtn = document.createElement("button");
                let timesIcon   = document.createElement('i');


                newListItemMention.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center")
                newListBadge.classList.add("badge", "spanEntity");
                newRemoveBtn.classList.add("btn", "btn-danger", "btn-sm");
                timesIcon.classList.add("fa", "fa-times");


                newListItemMention.id = "list-"+label+"-"+mention;
                newListBadge.id = "list-badge-"+label+"-"+mention;
                newRemoveBtn.id = "remove/$-$/"+label+"/$-$/"+mention;

                newRemoveBtn.addEventListener("click", RemoveAllItems)

                let textMention = document.createTextNode(mention);
                //newListItemMention.textContent = mention;
                newListBadge.textContent = "1";

                newRemoveBtn.appendChild(timesIcon);
                newListItemMention.appendChild(newRemoveBtn);
                newListItemMention.appendChild(textMention);

                newListItemMention.appendChild(newListBadge);
                labelList.appendChild(newListItemMention);
            }

            document.getElementById("entityLabelCount-"+label).textContent = actualCount+1;
            totalAnnotationsSpan.textContent = parseInt(totalAnnotationsSpan.textContent) + 1;
        }
        if (type === "less"){
            let mentionList = document.getElementById("list-"+label+"-"+mention);
            let itemListBadge   = document.getElementById("list-badge-"+label+"-"+mention);
            let actualBadgeCount = parseInt(itemListBadge.textContent);
            if (actualBadgeCount > 0) {
                itemListBadge.textContent = actualBadgeCount - 1;
            }
            let newActualBadgeCount = parseInt(itemListBadge.textContent);
            document.getElementById("entityLabelCount-"+label).textContent = actualCount-1;
            totalAnnotationsSpan.textContent = parseInt(totalAnnotationsSpan.textContent) - 1;
            if (newActualBadgeCount === 0){
                mentionList.remove();
            }

        }
    }

    // Remove all annotations for one label on text view and send information to backend
    function RemoveAllItems(event){
        spinnerLoadRemoveMeta.style.display = 'block';
        let target = event.target.closest('button');
        let itemList = target.id.split('/$-$/');
        let label = itemList[1];
        let mention = itemList[2];
        // request to get annotations corresponding to mention / label
        let data = {
            document_id:document_id,
            mention:mention,
            label:label,
        }
        async function requestAnnotationstoDelete() {
            let dataResponse;
            await sendData(data, '/return_annotations_to_delete').then(function (response) {
                return response.json()
            }).then(function (data) {
                dataResponse = data
            })
            return dataResponse
        }


        requestAnnotationstoDelete().then(function (annotations) {
            let index = annotations.length;
            for (let annotation in annotations){
                let currentAnnotation = annotations[annotation];
                currentAnnotation = Object.assign({}, currentAnnotation, {
                    documentID  : document_id,
                    projectID   : project_id
                });
                // send request to remove annotation
                async function remove () {
                    await sendData({destroyAll:false, destroyOne : currentAnnotation}, '/destroy_annotations');
                }
                remove().then();

                // remove annotation from Textcontent
                r.removeAnnotation(annotations[annotation]);
                // update list mentions
                updateListControl(annotations[annotation], 'less');
                index--;
                if (index === 0){
                    spinnerLoadRemoveMeta.style.display = 'none';
                }
            }
        })

    }

    // Reset list information
    function resetListsMentions(){
        const allListsMentions = document.querySelectorAll(".list-group");
        totalAnnotationsSpan.textContent = "0";
        allListsMentions.forEach(function (ele) {
            let label = ele.id.split('-')[1];
            document.getElementById("entityLabelCount-" + label).innerText = "0";
            ele.innerHTML = "";
        })
    }

    // Destroy all current annotations label independent

    function RemoveAllAnnotations(event){
        if (event.type === "click"){
            destroyAllHandler();
            resetListsMentions();
        }
    }

    // handler to send destroy all request
    function destroyAllHandler(){
        r.clearAnnotations().then(async function () {
            await sendData({destroyAll: true, destroyOne:false, id:document_id}, '/destroy_annotations');
        })
    }

    // listener for add span on hover
    function spanHandler(event) {
        let target = event.target;
        if (target.localName === "span" && target.className.split(' ')[0] === "r6o-annotation") {
            if (event.type === 'mouseover') {
                if(target.children.length === 0){
                    let newSpanLabel = document.createElement('span');
                    newSpanLabel.textContent = target.className.split(' ')[1];
                    newSpanLabel.classList.add("entityDescriptor", "spanEntity");
                    target.appendChild(newSpanLabel);
                }
            }
            if (event.type === "mouseout") {
                if (target.lastChild.classList[0] === "entityDescriptor" ){
                    target.removeChild(target.lastChild);
                }
            }
        }
    }

    // listener to open current list information
    function listHandler(event) {
        let span
        let target = event.target;
        if (event.type === "click"){
            if (((target.localName === "span") && (target.id === 'entityLabel')) || (target.localName === "i")){
                if(target.localName === "i"){
                    span = target.parentNode;
                }else{
                    span = target;
                }
                let label = span.className;
                let btnlist = document.getElementById("list-"+label);
                if (btnlist.style.display === "block"){
                    btnlist.style.display = "none";
                }else{
                    btnlist.style.display = "block";
                }
            }
        }
    }

    // return value of px info
    function getPxSize(el) {
        return el.match(/(\d+)px/)[1];
    }

    // listener to zoom in or zoom out
    function zoomText(event){
        let fontSizePre = textPre.getPropertyValue('font-size');
        let actualFS = parseFloat(getPxSize(fontSizePre));
        if(event.type === "click"){
            if (event.target.title === "zoom in" && actualFS !== 30){
                actualFS = actualFS + 5;
                textContent.style.fontSize = actualFS+"px";
            }
            else if (event.target.title === "zoom out" && actualFS > 10){
                actualFS = actualFS - 5;
                textContent.style.fontSize = actualFS+"px";
            }
        }
    }

    // Show or hide ul elements
    function displayUl(type){
        document.querySelectorAll('.list-group').forEach(function(ul){
            ul.style.display = type;
        });
    }

    // Query mentions in lists
    function queryMentions(event) {
        let i;
        let query = searchInput.value.toLowerCase().trim();
        let elements = document.querySelectorAll('.list-group > li');
        if (event.type === "focus"){
            displayUl('block');
        }
        else if (event.type === "keyup"){
            for (i = 0; i < elements.length; i ++) {
                let el = elements[i];
                if (el.innerText.replace(/[0-9]/g, '').toLowerCase().trim().indexOf(query)  > -1){
                    el.setAttribute('style', 'display: "" !important');
                }
                else{
                    el.setAttribute('style', 'display: none !important');
                }
            }
        }
        else if (event.type === "blur" && query.length === 0){
            displayUl('none');
        }
        else if (event.type === "click"){
            for (i = 0; i < elements.length; i ++) {
                let el = elements[i];
                el.setAttribute('style', 'display: ""');
            }
            displayUl('none')
            searchInput.value = "";
        }
    }

})();

