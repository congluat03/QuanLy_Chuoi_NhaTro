
    // JavaScript for image preview
    function setupImagePreview(inputId, previewDivId, previewImgId) {
        const input = document.getElementById(inputId');
        const previewDiv = document.getElementById(previewDivId');
        const previewImg = document.getElementById(previewImgId');

        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    previewDiv.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            } else {
                previewDiv.classList.add('hidden');
            }
        });
    }

    // Setup preview for front and back images
    setupImagePreview('file-front', 'preview-front', 'preview-front-img');
    setupImagePreview('file-back', 'preview-back', 'preview-back-img');
