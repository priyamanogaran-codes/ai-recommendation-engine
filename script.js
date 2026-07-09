function searchProduct(){

let input=document.getElementById("search").value.toLowerCase();

let cards=document.getElementsByClassName("card");

for(let i=0;i<cards.length;i++){

let name=cards[i].getElementsByTagName("h3")[0];

if(name.innerHTML.toLowerCase().includes(input)){

cards[i].style.display="block";

}

else{

cards[i].style.display="none";

}

}

}