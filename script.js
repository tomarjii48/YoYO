async function send(){
  let t=document.getElementById('msg').value.trim();
  if(!t) return;
  appendMessage('me', t);
  document.getElementById('msg').value='';
  const resp=await fetch('/webchat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
  const data=await resp.json();
  appendMessage('bot', data.reply);
}
function appendMessage(who, text){
  let c=document.getElementById('chat');
  let div=document.createElement('div'); div.className=who;
  let span=document.createElement('span'); span.className='bubble'; span.innerText=text;
  div.appendChild(span); c.appendChild(div); c.scrollTop=c.scrollHeight;
}
async function uploadFile(){
  const fi=document.getElementById('fileinput');
  if(!fi.files.length) return alert('Select a file');
  let fd=new FormData(); fd.append('file', fi.files[0]);
  let res=await fetch('/upload', {method:'POST', body:fd});
  let j=await res.json();
  if(j.ok){
    appendMessage('me', 'Uploaded image: '+j.filename);
    appendMessage('bot', 'To ask about this image, type: img:'+j.filename+' Your question');
  } else {
    appendMessage('bot','Upload failed');
  }
}
