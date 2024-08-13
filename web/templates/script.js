"use strict";

const form0 = document.getElementById("form0");
const form1 = document.getElementById("form1");
const form1a = document.getElementById("form1a");
const form2 = document.getElementById("form2");
const finalResult = document.getElementById("result");

const progressEl = document.getElementById("progress");
const circles = document.querySelectorAll(".circle");

let currentActive = 1;

let subject;
let brainImage;
let brainLesionMask;
let lesionImage;
let type;
let age;
let skipStepOne = false;

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
  const inputs = ths.querySelectorAll("input");

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
  return files
}

function startRun(event) {
  event.preventDefault();
  const inputsValid = validateInputs(form0);
  if (inputsValid) {
    const blah = document.getElementById('yes');
    if(blah.checked) {
      console.log("yes selected")
      skipStepOne = true
      form0.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
      form1a.style.left = "25px";
      // next slide
      incrementNumber();
      // update progress bar
      update();
    } else {
      skipStepOne = false
      console.log("no selected")
      form0.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
      form1.style.left = "25px";
    }
  }
}
//=============== Back Start==================
function backStart() {
  form0.style.left = "25px";
  if(skipStepOne) {
    form1a.style.setProperty('left', 'calc(var(--containerWidth) + 50px)');
  } else {
    form1.style.setProperty('left', 'calc(var(--containerWidth) + 50px)');
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

async function nextOneA(event) {
  event.preventDefault();
  const inputsValid = validateInputs(form1a);
  if (inputsValid) {

    // set loading state and disable inputs
    form1a.classList.add("loading");
    disableInputs(form1a)

    // get inputs and pass to python function
    subject = document.getElementById('subjectIDA').value;
    lesionImage = document.getElementById('lesionImage').value;
    age = document.getElementById('gestationalAgeA').value;

    const runsDir = document.getElementById("runsFolder").value
    let result = null
    if (skipStepOne) {
      result = await eel.step1A(runsDir, subject, lesionImage, age)();
    }


    console.log({ result })

    if (result) {
      form1a.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
      finalResult.style.left = "25px";

      document.getElementsByClassName('output')[0].style.display = 'block';

      document.getElementById("lesionOutput").innerText = lesionImage
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
    enableInputs(form1a);
    form1a.classList.remove("loading");
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
  const result = await eel.step2(runsDir, subject, brainLesionMask, age, 0, type)();

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
    if (indx < currentActive) {
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
  const next1a = document.getElementById("next1a");
  const generate = document.getElementById("generateDisconnectome");

  const back0 = document.getElementById("back0");
  const back0a = document.getElementById("back0a");
  const back1 = document.getElementById("back1");

  // start
  start.addEventListener("click", startRun);
  // next1
  next1.addEventListener("click", nextOne);
  // next1a
  next1a.addEventListener("click", nextOneA);

  // backStart
  back0.addEventListener("click", backStart);
  // backStart
  back0a.addEventListener("click", backStart);
  // back1
  back1.addEventListener("click", backOne);


  // submit
  generate.addEventListener("click", generateDisconnectome);
};
document.addEventListener("DOMContentLoaded", btnsEvents);

function expandAll() {
  document.querySelector('#json').expandAll()
}

function collapseAll() {
  document.querySelector('#json').collapseAll()
}

async function getFolder(event) {
  event.preventDefault();
  const folder_path = await eel.getFolder()();
  if (folder_path.length) {
    document.querySelector('#runsFolder').value = folder_path
    const files = await showRunsDirectory(folder_path)
    document.querySelector('#json').data = JSON.parse(files);
  }
}

async function getFile(event) {
  event.preventDefault();
  const file_path = await eel.getFile()();
  if (file_path) {
    event.target.value = file_path
  }
}
