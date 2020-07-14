
var active_id = null;

function getCoords(elem) {
  let box = elem.getBoundingClientRect();

  return {
    top: box.top + window.pageYOffset,
    left: box.left + window.pageXOffset
  };
}

//toggle dropdown show/hide
function toggleDiv(div_id) {
button_id = div_id.concat('-button');

elem = document.getElementById(button_id);
celem = document.getElementById(div_id);

if (active_id != null) {
active_elem = document.getElementById(active_id);
 if (active_elem.style.display === "block") {
        active_elem.style.display = "none";
        
    if (active_id === div_id) {
      return;
      }
      }
      
      
}


let coords = getCoords(elem);


  if (celem.style.display === "none") {
    celem.style.display = "block";
  } else {
    celem.style.display = "none";
  }
  celem.style.position = "absolute";
  celem.style.left = coords.left+ "px";
  celem.style.top = coords.top + 40 + "px";
  celem.style.width = "360px";
  //celem.style.height = "320px";
  active_id = div_id;
  

  
}

function toggleDivWrapper(div_id) {
 document.getElementById(div_id).classList.toggle("show-dd");
  

}



// prevent closing the dropdown when user toggles checkbox inside the dropdown
  var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var dd = dropdowns[i];
      dd.addEventListener('click', function (event) { 
            
            event.stopPropagation(); 
        }); 
    }

// close dropdown when user clicks outside
window.onclick = function(event) {
  if (!event.target.matches('.dropbtn'))  {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show-dd')) {
        openDropdown.classList.remove('show-dd');
      }
    }
  }
}