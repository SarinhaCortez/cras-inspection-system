function loadFiles(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('preview-container');
    previewContainer.innerHTML = ''; 

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.type === 'image/jpeg') {
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
            console.log(`File ${file.name}  a JPG image and will be ignored.`);
        }
    }
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

function handleFolderSelect() {
    document.getElementById('folder').click();
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

function handleFolderSelect() {
    document.getElementById('folder').click();
}

document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');

    dropArea.addEventListener('drop', handleDrop);
    dropArea.addEventListener('dragover', handleDragOver);
    dropArea.addEventListener('dragleave', handleDragLeave);
    dropArea.addEventListener('click', handleClick);
});
