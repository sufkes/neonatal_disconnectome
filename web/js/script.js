"use strict";

/* Form html elements */
const formHeaderText = document.getElementById("formHeaderText")
const startNewRunForm = document.getElementById("startNewRunForm");
const warpSubjectToAgeMatchedForm = document.getElementById("warpSubjectToAgeMatchedForm");
const form1a = document.getElementById("form1a");
const generateDisconnectomeForm = document.getElementById("generateDisconnectomeForm");
const finalResult = document.getElementById("result");

const nextButton = document.getElementById("next");

let inputs = startNewRunForm.querySelectorAll('input, select');
const progressBar = document.querySelector('.progress-fill');


/* Input fields Elements */
const runsInputField = document.getElementById("runsFolder");

/* Modal Elements */
const loadingModal = document.getElementById("loadingModal");

let percent = 0;
let subject;
let brainImage;
let brainLesionMask;
let lesionImage;
let type;
let age;
let skipStepOne = false;
let currentForm = "startNewRunForm"

let runsFolder = ""

//================= file Events ===================

async function getFolder(event) {
  event.preventDefault();
  const button = event.target;

  button.style.pointerEvents = 'none'; // disables further clicks
  button.style.opacity = '0.5'; // optional: visually indicate disabled state
  const folder_path = await eel.getFolder()();
  if (folder_path.length) {
    runsFolder = folder_path
    runsInputField.value = folder_path
  }
  button.style.pointerEvents = 'auto'; // re-enable clicks
  button.style.opacity = '1';           // reset visual
}

async function showSavedFolder() {
  try {
      const folderPath = await eel.get_saved_folder()();
      // Optionally display in the UI
      document.getElementById('runsFolder').value = folderPath || "No folder selected yet";
  } catch (error) {
      console.error("Error getting saved folder:", error);
  }
}

window.onload = function() {
  showSavedFolder();
};

async function getFile(event) {
  event.preventDefault();
  const element = event.target.nextElementSibling
  const filename = "brain_image_thumbnail_"+ Date.now() + ".png"
  const elements = document.getElementsByClassName('fileButton');

  for (var i = 0; i < elements.length; i++) {
    elements[i].style.pointerEvents = 'none'; // disables further clicks
    elements[i].style.opacity = '0.5'; // optional: visually indicate disabled state
  }


  const file_path = await eel.getFile(element.id === "3DBrainImage", filename)();
  if (file_path) {
    element.value = file_path
    validateInput(element)
    let inputDataElement;
    if(element.id === "3DBrainImage") {
      const parent = document.getElementById("3DBrainImageFigure")
      parent.children[0].src = "../img/" + filename;
      parent.classList.remove("hide")
      inputDataElement = document.getElementById("brainImageInput")
    } else if(element.id === "3DBrainLesionMask") {
      inputDataElement = document.getElementById("brainLesionMaskInput")
    } else if(element.id === "lesionImage") {
      inputDataElement = document.getElementById("lesionInput")
    }
    inputDataElement.innerText = file_path
    inputDataElement.previousElementSibling.classList.remove("grayscale")
    inputDataElement.previousElementSibling.classList.add("success")
    inputDataElement.parentNode.classList.remove("hide")
  }
  for (var i = 0; i < elements.length; i++) {
    elements[i].style.pointerEvents = 'auto'; // re-enable clicks
    elements[i].style.opacity = '1';           // reset visual
  }

}

//=============== Form utils ==================

function updateProgress() {
    const totalFields = inputs.length;
    let completedFields = 0;

    inputs.forEach(input => {
        if (input.value.length > 0) completedFields++;
    });

    const progress = (completedFields / totalFields) * 100;
    progressBar.style.width = `${progress}%`;
    progressBar.parentElement.setAttribute('aria-valuenow', progress);
}

function validateInput(input) {
    let errorElement = document.getElementById(`${input.id}Error`);
    let isValid = true;

    if (input.id === "gestationalAge" || input.id === "gestationalAgeA") {
      if(input.value < 28 || input.value > 44) {
        isValid = false
      }
    } else if (input.id === "subjectID" || input.id === "subjectIDA") {
      const subjectIDRegex = /^[a-zA-Z0-9]+$/;
      isValid = subjectIDRegex.test(input.value);
    } else if(input.type === "radio") {
      const radioButtons = document.querySelectorAll(`input[name="${input.name}"]`);
      for (const radioButton of radioButtons) {
        if (radioButton.checked) {
          isValid = true
          break;
        } else {
          isValid = false;
        }
      }
      errorElement = document.getElementById(`${input.name}Error`);
    } else {
      isValid = input.value.length > 0;
    }

    if (!isValid) {
        input.classList.remove('valid');
        input.classList.add('invalid');
        errorElement?.classList.add('visible');
    } else {
        input.classList.remove('invalid');
        input.classList.add('valid');
        errorElement?.classList.remove('visible');
    }

    updateProgress();
    return isValid;
}

const inputsEvents = () => {
  inputs.forEach(input => {
    input.addEventListener('blur', () => validateInput(input));
    input.addEventListener('input', () => validateInput(input));
  });
};
document.addEventListener("DOMContentLoaded", inputsEvents);



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
  let isFormValid = true;
  const inputs = ths.querySelectorAll("input, select");

  inputs.forEach(input => {
    if (!validateInput(input) || !input.checkValidity()) {
        isFormValid = false;
    }
  });

  if (isFormValid) {
    progressBar.style.width = '0%';
    inputs.forEach(input => input.classList.remove('valid'));
  }

  return isFormValid;
}

function hideForm(form) {
  form.style.setProperty('left', 'calc(-1* (var(--containerWidth) + 50px))');
  form.style.setProperty('display', 'none')
  form.classList.remove("active")
}

function showForm(form) {
  form.style.left = "25px";
  form.style.setProperty('display', 'block')
  form.classList.add("active")
}

//============== Core Form Functionality ===============

async function startRun() {
  const inputsValid = validateInputs(startNewRunForm);
  if (inputsValid) {
    await eel.deleteImageFiles()();
    const skipStep = document.getElementById('yes');
    hideForm(startNewRunForm)
    if(skipStep.checked) {
      formHeaderText.innerText = "Generate Disconnectome";
      skipStepOne = true
      showForm(form1a)
      currentForm = "form1a"
      inputs = form1a.querySelectorAll('input, select');
    } else {
      formHeaderText.innerText = "Warp Subject Image and Lesion Mask To Age Matched Template";
      skipStepOne = false
      showForm(warpSubjectToAgeMatchedForm)
      currentForm = "warpSubjectToAgeMatchedForm"
      inputs = warpSubjectToAgeMatchedForm.querySelectorAll('input, select');
    }
    inputsEvents()
    nextButton.setAttribute("form", currentForm)
  }
}


async function nextOne() {
  const inputsValid = validateInputs(warpSubjectToAgeMatchedForm);
  if(inputsValid) {
    // set loading state and disable inputs
    showLoading("Warping Subject To Age Matched Template");
    disableInputs(warpSubjectToAgeMatchedForm)

    // get inputs and pass to python function
    subject = document.getElementById('subjectID').value;
    brainImage = document.getElementById('3DBrainImage').value;
    brainLesionMask = document.getElementById('3DBrainLesionMask').value;
    type = document.getElementById('brainType').value;
    age = document.getElementById('gestationalAge').value;

    const runsDir = runsInputField.value
    const filenameHash = Date.now().toString()

    const result = await eel.step1(runsDir, subject, type, brainImage, brainLesionMask, age, filenameHash)();

    if(result) {
      formHeaderText.innerText = "Generate Disconnectome";
      hideForm(warpSubjectToAgeMatchedForm)
      showForm(generateDisconnectomeForm)
      currentForm = "generateDisconnectomeForm"
      inputs = generateDisconnectomeForm.querySelectorAll('input, select');

      const figure1 = document.getElementById("plotAlignedImagePair")
      const figure2 = document.getElementById("lesionOnOriginalTemplateClusters")
      const figure3 = document.getElementById("lesionOnAgeMatchedTemplateClusters")

      figure1.src =
      "../img/plot_aligned_image_pair_" + filenameHash + ".png";

      figure2.src = "../img/lesion_on_original_" + filenameHash + ".png";

      figure3.src = "../img/lesion_on_age_matched_template_clusters_" + filenameHash + ".png";

      setOutputData("brainImageWarpedOutput", age, runsDir, subject)
      setOutputData("lesionImageWarpedOutput", age, runsDir, subject)
      setOutputData("ageMatchedTemplateOutput",age, runsDir, subject, type)

      // remove loading state and re-enable inputs
      enableInputs(warpSubjectToAgeMatchedForm);
      inputsEvents()
      nextButton.setAttribute("form", currentForm)
      stopLoading();
    } else {
      // TODO: Show error
      showError()
    }
  }
}

async function nextOneA() {
  const inputsValid = validateInputs(form1a);
  if (inputsValid) {
    // set loading state and disable inputs
    showLoading("Generating Disconnectome");
    disableInputs(form1a)

    // get inputs and pass to python function
    subject = document.getElementById('subjectIDA').value;
    lesionImage = document.getElementById('lesionImage').value;
    age = document.getElementById('gestationalAgeA').value;

    const runsDir = runsInputField.value
    let result = null
    const filenameHash = Date.now().toString();
    if (skipStepOne) {
      result = await eel.step1A(runsDir, subject, lesionImage, age, filenameHash)();
    }

    if (result) {
      formHeaderText.innerText = "Run Finished";
      nextButton.classList.add("hide")
      hideForm(form1a)
      finalResult.style.left = "25px";
      finalResult.style.setProperty('display', 'block')

      document.querySelector('#plotDisconnectomeAtLesionCentroids').src = "../img/disconnectome_at_lesion_centroids_" + filenameHash + ".png";

      document.querySelector('#plotDisconnectomeAtLesionCentroids').parentElement.classList.remove("hide");

      setOutputData("disconnectomeOutput", age, runsDir, subject)
      setOutputData("lesionImageIn40wOutput", age, runsDir, subject)
      // remove loading state and re-enable inputs
      enableInputs(form1a);
      stopLoading();
    } else {
      showError();
    }
  }
}


//=============== Generate Disconnectome ==================
async function generateDisconnectome() {
  // set loading state and disable inputs
  showLoading("Generating Disconnectome");
  const runsDir = runsInputField.value;
  const filenameHash = Date.now().toString();
  const result = await eel.step2(runsDir, subject, brainLesionMask, age, filenameHash, 0, type)();

  if (result) {
    formHeaderText.innerText = "Run Finished";
    hideForm(generateDisconnectomeForm)

    nextButton.classList.add("hide")

    finalResult.style.left = "25px";
    finalResult.style.setProperty('display', 'block')


    document.querySelector('#plotDisconnectomeAtLesionCentroids').src =
      "../img/disconnectome_at_lesion_centroids_" + filenameHash + ".png";

    document.querySelector('#plotDisconnectomeAtLesionCentroids').parentElement.classList.remove("hide");

    setOutputData("disconnectomeOutput", age, runsDir, subject)
    setOutputData("lesionImageIn40wOutput", age, runsDir, subject)
    setOutputData("40wTemplateImageOutput",age, runsDir, subject, type)

    // remove loading state and re-enable inputs
    stopLoading();
  } else {
    showError();
  }
}


//================= btn Events ===================

function next(event) {
  event.preventDefault();
  const id = event.target.getAttribute("form");

  switch (id) {
    case "startNewRunForm":
      startRun();
      break;
    case "warpSubjectToAgeMatchedForm":
      nextOne();
      break;
    case "form1a":
      nextOneA();
      break;
    case "generateDisconnectomeForm":
      generateDisconnectome();
      break;
    default:
      break;
  }

}




const btnsEvents = () => {
  // next
  nextButton.addEventListener("click", next);
};
document.addEventListener("DOMContentLoaded", btnsEvents);

function setOutputData(id, age, runsDir, subject, type = "T1w") {
  let outputDataElement;
  let val;
  let roundedAge = Math.round(age)
  if(roundedAge < 28) {
    roundedAge = 28
  }
  if(roundedAge > 44) {
    roundedAge = 44
  }
  const templateSpacePrefix = runsDir + "/" + subject + "/template_space/" + roundedAge + "W/"
  const templateSpaceSuffix = roundedAge + "-week-template-space-warped.nii.gz"

  const disconnectomePrefix = runsDir + "/" + subject + "/disconnectome/"
  switch (id) {
    case "brainImageWarpedOutput":
      outputDataElement = document.getElementById("brainImageWarpedOutput")
      val =  templateSpacePrefix + "brain_img_" + templateSpaceSuffix
      break;
    case "lesionImageWarpedOutput":
      outputDataElement = document.getElementById("lesionImageWarpedOutput")
      val = templateSpacePrefix + "lesion_mask_" + templateSpaceSuffix
      break;
    case "ageMatchedTemplateOutput":
      outputDataElement = document.getElementById("ageMatchedTemplateOutput")
      val = runsDir.split("/runs")[0] + "/template/templates/week" + roundedAge + "_" + type + ".nii.gz"
      break;
    case "disconnectomeOutput":
      outputDataElement = document.getElementById("disconnectomeOutput")
      val = disconnectomePrefix + "disconnectome-threshold_0.nii.gz"
      break;
    case "lesionImageIn40wOutput":
      outputDataElement = document.getElementById("lesionImageIn40wOutput")
      val = disconnectomePrefix + "lesion_mask_40-week-template-space-warped.nii.gz"
      break;
    case "40wTemplateImageOutput":
      outputDataElement = document.getElementById("40wTemplateImageOutput")
      val = runsDir.split("/runs")[0] + "/template/templates/week40_" + type + ".nii.gz"
      break;
    default:
      break;
  }
  updateRunData(outputDataElement, val)
}


function setInputData(event) {
  event.preventDefault();
  let inputDataElement;
  const id = event.target.id

  switch (id) {
    case "brainType":
      inputDataElement = document.getElementById("typeInput")
      break;
    case "subjectID":
    case "subjectIDA":
      inputDataElement = document.getElementById("subjectInput")
      break;
    case "gestationalAge":
    case "gestationalAgeA":
      inputDataElement = document.getElementById("ageInput")
      break;
    default:
      break;
  }
  updateRunData(inputDataElement, event.target.value)
}

function updateRunData(element, value) {
  element.innerText = value
  element.previousElementSibling.classList.remove("grayscale")
  element.previousElementSibling.classList.add("success")
  element.parentNode.classList.remove("hide")
}



function showLoading(modalText = "Computing Result") {
  document.getElementById("loadingModalLabel").classList.add("hide")
  document.getElementById("loadingModalClose").classList.add("hide")

  document.getElementById("loadingModalContent").innerHTML = `
  ${modalText}
  <p>This computation will take approximately 30s - 2min</p>
  `
  loadingModal.showModal();
}

function stopLoading() {
  loadingModal.close();
}

function showError() {
  document.getElementById("loadingModalLabel").classList.remove("hide")
  document.getElementById("loadingModalClose").classList.remove("hide")
  document.getElementById("loadingModalContent").innerHTML = `
    An error occured and the operation failed
  `
  document.getElementById("circlePercentLoader").classList.add("hide")
}
