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


function changedColor() {
    var newRGBHex = document.getElementById("colorPicker").value;
    var newRGBValues = hexToRgb(newRGBHex);
    const request = new XMLHttpRequest();
    request.open('POST', '/ProcessNewColor/${JSON.stringify(newRGBValues)}');
    request.send();
    window.alert(newRGBValues);
}

//function changedColor() {
//    const colorPicker = document.getElementById('colorPicker');
//    const colorValue = colorPicker.value;
//    fetch('/get_color', {
//        method: 'POST',
//        body: JSON.stringify({color: colorValue}),
//        headers: {'Content-Type': 'application/json'}
//    });
//}

function hexToRgb(hex){
    var c;
    if(/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)){
        c= hex.substring(1).split('');
        if(c.length== 3){
            c= [c[0], c[0], c[1], c[1], c[2], c[2]];
        }
        c= '0x'+c.join('');
        return [(c>>16)&255, (c>>8)&255, c&255].join(',');
    }
    throw new Error('Bad Hex');
}
