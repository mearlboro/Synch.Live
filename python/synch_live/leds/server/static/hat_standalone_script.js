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
  document.getElementById("defaultOpen").click();
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
