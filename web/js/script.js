"use strict";

const $formHeaderText = document.getElementById("formHeaderText")
const startNewRunForm = document.getElementById("startNewRunForm");
const warpSubjectToAgeMatchedForm = document.getElementById("warpSubjectToAgeMatchedForm");
const form1a = document.getElementById("form1a");
const generateDisconnectomeForm = document.getElementById("generateDisconnectomeForm");
const finalResult = document.getElementById("result");

const progressEl = document.getElementById("progress");
const circles = document.querySelectorAll(".circle");


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
    let valid = inputs[i].checkValidity();
    if(inputs[i].id === "gestationalAge" || inputs[i].id === "gestationalAgeA") {
      if(inputs[i].value < 28 || inputs[i].value > 48) {
        inputs[i].nextElementSibling.innerText = "Age outside of range: 28-48"
        inputs[i].nextElementSibling.classList.add("label")
      } else {
        inputs[i].nextElementSibling.innerText = ""
        inputs[i].nextElementSibling.classList.remove("label")
      }
    }
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

async function startRun(event) {
  event.preventDefault();
  const inputsValid = validateInputs(startNewRunForm);
  if (inputsValid) {
    await eel.deleteImageFiles()();
    const skipStep = document.getElementById('yes');
    startNewRunForm.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
    startNewRunForm.style.setProperty('display', 'none')
    if(skipStep.checked) {
      $formHeaderText.innerText = "Generate Disconnectome";
      skipStepOne = true
      form1a.style.left = "25px";
      form1a.style.setProperty('display', 'block')
    } else {
      $formHeaderText.innerText = "Warp Subject Image and Lesion Mask To Age Matched Template";
      skipStepOne = false
      warpSubjectToAgeMatchedForm.style.left = "25px";
      warpSubjectToAgeMatchedForm.style.setProperty('display', 'block')
    }
  }
}
//=============== Back Start==================
function backStart() {
  startNewRunForm.style.left = "25px";
  startNewRunForm.style.setProperty('display', 'block')
  $formHeaderText.innerText = "Start a new run";
  if(skipStepOne) {
    form1a.style.setProperty('left', 'calc(var(--containerWidth) + 50px)');
    form1a.style.setProperty('display', 'none')
  } else {
    warpSubjectToAgeMatchedForm.style.setProperty('left', 'calc(var(--containerWidth) + 50px)');
    warpSubjectToAgeMatchedForm.style.setProperty('display', 'none')
  }

}
//============== Next Form===============
async function nextOne(event) {
  event.preventDefault();
  const inputsValid = validateInputs(warpSubjectToAgeMatchedForm);
  if(inputsValid) {
    // set loading state and disable inputs
    warpSubjectToAgeMatchedForm.classList.add("loading");
    disableInputs(warpSubjectToAgeMatchedForm)

    // get inputs and pass to python function
    subject = document.getElementById('subjectID').value;
    brainImage = document.getElementById('3DBrainImage').value;
    brainLesionMask = document.getElementById('3DBrainLesionMask').value;
    type = document.getElementById('brainType').value;
    age = document.getElementById('gestationalAge').value;

    const runsDir = document.getElementById("runsFolder").value

    const filenameHash = Date.now().toString()

    const result = await eel.step1(runsDir, subject, type, brainImage, brainLesionMask, age, filenameHash)();

    if(result) {
      $formHeaderText.innerText = "Generate Disconnectome";
      warpSubjectToAgeMatchedForm.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
      warpSubjectToAgeMatchedForm.style.setProperty('display', 'none')
      generateDisconnectomeForm.style.left = "25px";
      generateDisconnectomeForm.style.setProperty('display', 'block')

      document.getElementsByClassName('output')[0].style.display = 'block';

      document.getElementById("brainImageOutput").innerText = brainImage
      document.getElementById("brainLesionMaskOutput").innerText = brainLesionMask
      document.getElementById("typeOutput").innerText = type
      document.getElementById("subjectOutput").innerText = subject
      document.getElementById("ageOutput").innerText = age
    }

    const figure1 = document.getElementById("plotAlignedImagePair")
    const figure2 = document.getElementById("lesionOnOriginalTemplateClusters")
    const figure3 = document.getElementById("lesionOnAgeMatchedTemplateClusters")

    figure1.src =
    "../img/plot_aligned_image_pair_" + filenameHash + ".png";

    figure2.src = "../img/lesion_on_original_" + filenameHash + ".png";

    figure3.src = "../img/lesion_on_age_matched_template_clusters_" + filenameHash + ".png";

    // remove loading state and re-enable inputs
    enableInputs(warpSubjectToAgeMatchedForm);
    warpSubjectToAgeMatchedForm.classList.remove("loading");
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
    const filenameHash = Date.now().toString();
    if (skipStepOne) {
      result = await eel.step1A(runsDir, subject, lesionImage, age, filenameHash)();
    }

    if (result) {
      $formHeaderText.innerText = "Run Finished";
      form1a.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
      form1a.style.setProperty('display', 'none')
      finalResult.style.left = "25px";
      finalResult.style.setProperty('display', 'block')

      document.getElementsByClassName('output')[0].style.display = 'block';

      document.getElementById("lesionOutput").innerText = lesionImage
      document.getElementById("subjectOutput").innerText = subject
      document.getElementById("ageOutput").innerText = age

    }

    document.querySelector('#plotDisconnectomeAtLesionCentroids').src = "../img/disconnectome_at_lesion_centroids_" + filenameHash + ".png";

    document.querySelector('#plotDisconnectomeAtLesionCentroids').parentElement.classList.remove("hide");

    // remove loading state and re-enable inputs
    enableInputs(form1a);
    form1a.classList.remove("loading");
  }
}
//=============== Back One==================
function backOne() {
  warpSubjectToAgeMatchedForm.style.left = "25px";
  warpSubjectToAgeMatchedForm.style.setProperty('display', 'block')
  generateDisconnectomeForm.style.setProperty('left', 'calc(var(--containerWidth) + 50px)');
  generateDisconnectomeForm.style.setProperty('display', 'none')
}
//=============== Generate Disconnectome ==================
async function generateDisconnectome(event) {
  event.preventDefault();

  // set loading state and disable inputs
  generateDisconnectomeForm.classList.add("loading");
  const runsDir = document.getElementById("runsFolder").value;
  const filenameHash = Date.now().toString();
  const result = await eel.step2(runsDir, subject, brainLesionMask, age, filenameHash, 0, type)();

  if (result) {
    $formHeaderText.innerText = "Run Finished";
    generateDisconnectomeForm.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
    generateDisconnectomeForm.style.setProperty('display', 'none')
    finalResult.style.left = "25px";
    finalResult.style.setProperty('display', 'block')
  }

  document.querySelector('#plotDisconnectomeAtLesionCentroids').src =
    "../img/disconnectome_at_lesion_centroids_" + filenameHash + ".png";

  document.querySelector('#plotDisconnectomeAtLesionCentroids').parentElement.classList.remove("hide");

  // remove loading state and re-enable inputs
  generateDisconnectomeForm.classList.remove("loading");

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


async function getFolder(event) {
  event.preventDefault();
  const folder_path = await eel.getFolder()();
  if (folder_path.length) {
    document.querySelector("#runsFolder").value = folder_path
  }
}

async function getFile(event) {
  event.preventDefault();
  let element = event.target
  if(event.target.classList.contains('fileButton')) {
    element = event.target.nextElementSibling
  }
  const filename = "brain_image_thumbnail_"+ Date.now() + ".png"
  const file_path = await eel.getFile(element.id === "3DBrainImage", filename)();
  if (file_path) {
    if(element.id === "3DBrainImage") {
      element.value = file_path
      const parent = element.parentElement.nextElementSibling
      parent.children[0].src = "../img/" + filename;
      parent.classList.remove("hide")
    } else if(element.id === "3DBrainLesionMask") {
      element.value = file_path
    } else if(element.id === "lesionImage") {
      element.value = file_path
    }
  }
}

async function preview(event) {
  event.preventDefault();
  document.getElementById("previewResultImages").classList.remove("hide")
}

