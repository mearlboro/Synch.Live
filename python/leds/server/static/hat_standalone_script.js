function openTab(evt, tabName) {
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

function loadCustomOnLoad() {
    openTab(event, 'Colour');
}

window.onload = loadCustomOnLoad;

const blickfrequencySlider = document.getElementById("blickfrequency");
const blickfrequencyValue = document.getElementById("blickfrequency-value");
blickfrequencyValue.innerHTML = blickfrequencySlider.value;

blickfrequencySlider.oninput = function() {
    blickfrequencyValue.innerHTML = this.value;
};

const effectdurationSlider = document.getElementById("effectduration");
const effectdurationValue = document.getElementById("effectduration-value");
effectdurationValue.innerHTML = effectdurationSlider.value;

effectdurationSlider.oninput = function() {
    effectdurationValue.innerHTML = this.value;
};

//document.getElementById("defaultOpen").click();
//
//$('.tablinks').click(function(){
//    var activetab = $(this).attr('id');
//    localStorage.setItem('activetab', activetab );
//});
//
//$(function() {  //short hand for $(document).ready()
//    var activetab = localStorage.getItem('activetab');
//    document.getElementById(activetab).click();
//});

//function changedColor() {
//    var newRGBHex = document.getElementById("colorPicker").value;
//    var newRGBValues = hexToRgb(newRGBHex);
//    const request = new XMLHttpRequest();
//    request.open('POST', '/ProcessNewColor/${JSON.stringify(newRGBValues)}');
//    request.send();
//    window.alert(newRGBValues);
//}
//
//function hexToRgb(hex){
//    var c;
//    if(/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)){
//        c= hex.substring(1).split('');
//        if(c.length== 3){
//            c= [c[0], c[0], c[1], c[1], c[2], c[2]];
//        }
//        c= '0x'+c.join('');
//        return [(c>>16)&255, (c>>8)&255, c&255].join(',');
//    }
//    throw new Error('Bad Hex');
//}