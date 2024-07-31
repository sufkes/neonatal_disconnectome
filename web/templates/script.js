"use strict";

const form0 = document.getElementById("form0");
const form1 = document.getElementById("form1");
const form2 = document.getElementById("form2");
const finalResult = document.getElementById("result");

const progressEl = document.getElementById("progress");
const circles = document.querySelectorAll(".circle");

let currentActive = 1;

let subject;
let brainImage;
let brainLesionMask;
let type;
let age;

function disableInputs(form) {
  [...form.elements].forEach(element => {
    element.setAttribute('disabled', "");
  });
}

function enableInputs(form) {
  [...form.elements].forEach(element => {
    element.removeAttribute("disabled");
  });
}
function validateInputs(ths) {
  let inputsValid = true;

  console.log({ths})
  const inputs = ths.querySelectorAll("input");

  console.log({inputs})
  for (let i = 0; i < inputs.length; i++) {
    const valid = inputs[i].checkValidity();
    if (!valid) {
      inputsValid = false;
      inputs[i].reportValidity();
      inputs[i].classList.add("invalid-input");
    } else {
      inputs[i].classList.remove("invalid-input");
    }
  }
  return inputsValid;
}

async function showRunsDirectory(dir) {
  const files = await eel.showFiles(dir)();
  console.log(JSON.parse(files))
  return files
}

function startRun(event) {
  console.log(event)
  event.preventDefault();
  const inputsValid = validateInputs(form0);
  console.log({ inputsValid })
  if (inputsValid) {
    console.log("do I get here")
    form0.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
    form1.style.left = "25px";
    // // next slide
    // incrementNumber();
    // // update progress bar
    // update();
  }
}
//============== Next Form===============
async function nextOne(event) {
  event.preventDefault();
  const inputsValid = validateInputs(form1);
  if(inputsValid) {

    // set loading state and disable inputs
    form1.classList.add("loading");
    disableInputs(form1)

    // get inputs and pass to python function
    subject = document.getElementById('subjectID').value;
    brainImage = document.getElementById('3DBrainImage').value;
    brainLesionMask = document.getElementById('3DBrainLesionMask').value;
    type = document.getElementById('brainType').value;
    age = document.getElementById('gestationalAge').value;

    const runsDir = document.getElementById("runsFolder").value
    const result = await eel.step1(runsDir, subject, type, brainImage, brainLesionMask, age)();

    console.log({result})

    if(result) {
      form1.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
      form2.style.left = "25px";

      document.getElementsByClassName('output')[0].style.display = 'block';

      document.getElementById("brainImageOutput").innerText = brainImage
      document.getElementById("brainLesionMaskOutput").innerText = brainLesionMask
      document.getElementById("typeOutput").innerText = type
      document.getElementById("subjectOutput").innerText = subject
      document.getElementById("ageOutput").innerText = age



      const files = await showRunsDirectory(runsDir)
      document.querySelector('#json').data = JSON.parse(files);

      // next slide
      incrementNumber();
      // update progress bar
      update();
    }

    // remove loading state and re-enable inputs
    enableInputs(form1);
    form1.classList.remove("loading");
  }
}
//=============== Back One==================
function backOne() {
  form1.style.left = "25px";
  form2.style.setProperty('left', 'calc(var(--containerWidth) + 50px)');
  // back slide
  decrementNumber();
  // update progress bar
  update();
}
//=============== Generate Disconnectome ==================
async function generateDisconnectome(event) {
  event.preventDefault();

  // set loading state and disable inputs
  form2.classList.add("loading");
  const runsDir = document.getElementById("runsFolder").value
  const result = await eel.step2(runsDir, subject, type, brainLesionMask, age)();

  console.log({ result })
  if (result) {
    form2.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
    finalResult.style.left = "25px";

    const files = await showRunsDirectory(runsDir)
    document.querySelector('#json').data = JSON.parse(files);

    // next slide
    incrementNumber();
    // update progress bar
    update();
  }

  // remove loading state and re-enable inputs
  form2.classList.remove("loading");

}

//============= Progress update====================
function update() {
  circles.forEach((circle, indx) => {
    console.log({circle})
    console.log({indx})
    console.log({ currentActive })
    if (indx < currentActive) {
      console.log("add active")
      circle.classList.add("active");
    } else {
      circle.classList.remove("active");
    }

    if (indx < currentActive - 1) {
      circle.getElementsByTagName('span')[0].style.display = "none"
      circle.getElementsByTagName('svg')[0].style.display = "block"
    } else {
      circle.getElementsByTagName('svg')[0].style.display = "none"
      circle.getElementsByTagName('span')[0].style.display = "block"
    }


    // get all of active classes
    const actives = document.querySelectorAll(".active");
    progressEl.style.width =
      ((actives.length - 1) / (circles.length - 1)) * 100 + "%";
  });
}
//================== Increament Number===============
function incrementNumber() {
  // next progress number
  currentActive++;
  if (currentActive > circles.length) {
    currentActive = circles.length;
  }
}
//================ Decreament Number=================
function decrementNumber() {
  currentActive--;
  if (currentActive < 1) {
    currentActive = 1;
  }
}
//================= btn Events===================
const btnsEvents = () => {
  const start = document.getElementById("start");
  const next1 = document.getElementById("next1");
  const generate = document.getElementById("generateDisconnectome");

  const back1 = document.getElementById("back1");

  // start
  start.addEventListener("click", startRun);
  // next1
  next1.addEventListener("click", nextOne);
  // back1
  back1.addEventListener("click", backOne);


  // submit
  generate.addEventListener("click", generateDisconnectome);
};
document.addEventListener("DOMContentLoaded", btnsEvents);
