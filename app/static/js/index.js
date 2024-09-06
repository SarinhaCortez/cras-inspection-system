function loadFiles(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('preview-container');
    previewContainer.innerHTML = ''; 

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.type === 'image/jpeg' || file.type === 'image/jpg' || file.type === 'image/png') {
            const imgContainer = document.createElement('div');
            imgContainer.classList.add('img-container');

            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);

            const closeIcon = document.createElement('span');
            closeIcon.classList.add('close-icon');
            closeIcon.innerHTML = '&times;';
            closeIcon.onclick = function() {
                previewContainer.removeChild(imgContainer);
            };

            imgContainer.appendChild(img);
            imgContainer.appendChild(closeIcon);
            previewContainer.appendChild(imgContainer);
        } else {
            console.log(`File ${file.name} is not a JPG image and will be ignored.`);
        }
    }
}

function handleFolderSelect() {
    document.getElementById('folder').click();
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    const files = event.dataTransfer.files;
    document.getElementById('file').files = files;
    loadFiles({ target: { files: files } });
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('drop-area').classList.add('hover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('drop-area').classList.remove('hover');
}

function handleClick() {
    document.getElementById('file').click();
}

document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');

    dropArea.addEventListener('drop', handleDrop);
    dropArea.addEventListener('dragover', handleDragOver);
    dropArea.addEventListener('dragleave', handleDragLeave);
    dropArea.addEventListener('click', handleClick);
});

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    const files = event.dataTransfer.files;
    document.getElementById('file').files = files;
    loadFiles({ target: { files: files } });
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('drop-area').classList.add('hover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('drop-area').classList.remove('hover');
}

function handleClick() {
    document.getElementById('file').click();
}


document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');

    dropArea.addEventListener('drop', handleDrop);
    dropArea.addEventListener('dragover', handleDragOver);
    dropArea.addEventListener('dragleave', handleDragLeave);
    dropArea.addEventListener('click', handleClick);
});

document.getElementById('predictForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var form = event.target;
    var button = document.getElementById('predict');
    
    button.disabled = true;
    button.textContent = 'Processing...';

    var formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json()) 
    .then(data => {
        console.log('Success:', data);
        button.disabled = false;
        button.textContent = 'Predict Value!';
        if (data.redirect) {
            window.location.href = data.redirect;
        }
        
    })
    .catch(error => {
        console.error('Error:', error);

        button.disabled = false;
        button.textContent = 'Predict Value!';
        
    });
});