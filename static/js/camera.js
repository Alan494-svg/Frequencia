const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const btnFoto = document.getElementById("capturar");
const fotoInput = document.getElementById("foto_base64");

async function iniciarCamera(){

    try{

        const stream =
        await navigator.mediaDevices.getUserMedia({
            video:true
        });

        video.srcObject = stream;

    }
    catch(e){

        alert("Não foi possível acessar a câmera.");

    }
}

if(video){
    iniciarCamera();
}

if(btnFoto){

    btnFoto.addEventListener("click",()=>{

        const ctx = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        ctx.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );

        const imagem =
        canvas.toDataURL("image/jpeg");

        fotoInput.value = imagem;

        alert("Foto capturada!");
    });

}