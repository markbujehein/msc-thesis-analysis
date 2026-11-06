// remembers which steps are ticked; works without storage
(function(){var k='thymol-tut:'+location.pathname.split('/').pop();var s={};try{s=JSON.parse(localStorage.getItem(k)||'{}')}catch(e){}
document.querySelectorAll('.step>input').forEach(function(b,i){b.checked=!!s[i];b.addEventListener('change',function(){s[i]=b.checked;try{localStorage.setItem(k,JSON.stringify(s))}catch(e){}})})})();
