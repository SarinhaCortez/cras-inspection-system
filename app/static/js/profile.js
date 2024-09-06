
function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = source.checked;
    });
}

function triggerFileInput() {
    document.getElementById('profile-pic-input').click();
}

function submitForm() {
    document.getElementById('profile-pic-form').submit();
}

function confirmDelete() {
    if (confirm("Are you sure you want to delete your account? You will loose your reports. This action cannot be undone.")) {
        document.getElementById('delete-account-form').submit();
    }
}