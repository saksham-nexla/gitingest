// Copy functionality
function copyText(className) {
    let textToCopy;

    if (className === 'directory-structure') {
    // For directory structure, get the hidden input value
        const hiddenInput = document.getElementById('directory-structure-content');

        if (!hiddenInput) {return;}
        textToCopy = hiddenInput.value;
    } else {
    // For other elements, get the textarea value
        const textarea = document.querySelector(`.${ className }`);

        if (!textarea) {return;}
        textToCopy = textarea.value;
    }

    const button = document.querySelector(`button[onclick="copyText('${className}')"]`);

    if (!button) {return;}

    // Copy text
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            // Store original content
            const originalContent = button.innerHTML;

            // Change button content
            button.innerHTML = 'Copied!';

            // Reset after 1 second
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        })
        .catch((err) => {
            console.error('Failed to copy text:', err);
            const originalContent = button.innerHTML;

            button.innerHTML = 'Failed to copy';
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        });
}

function getFileName(element) {
    const indentSize = 4;
    let path = '';
    let prevIndentLevel = null;

    while (element) {
        const line = element.textContent;
        const index = line.search(/[a-zA-Z0-9_.-]/);
        const indentLevel = index / indentSize;

        // Stop when we reach or go above the top-level directory
        if (indentLevel <= 1) {
            break;
        }
        if (prevIndentLevel === null || indentLevel === prevIndentLevel - 1) {
            const fileName = line.substring(index).trim();

            path = fileName + path;
            prevIndentLevel = indentLevel;
        }
        element = element.previousElementSibling;
    }

    return path;
}

function toggleFile(element) {
    const patternInput = document.getElementById('pattern');
    const patternFiles = patternInput.value
        ? patternInput.value.split(',').map((item) => item.trim())
        : [];

    const directoryContainer = document.getElementById('directory-structure-container');
    const treeLineElements = Array.from(directoryContainer.children).filter(
        (child) => child.tagName === 'PRE',
    );

    // Skip header and repository name
    if (treeLineElements.slice(0, 2).includes(element)) {
        return;
    }

    element.classList.toggle('line-through');
    element.classList.toggle('text-gray-500');

    const fileName = getFileName(element);
    const idx = patternFiles.indexOf(fileName);

    if (idx !== -1) {
        patternFiles.splice(idx, 1);
    } else {
        patternFiles.push(fileName);
    }

    patternInput.value = patternFiles.join(', ');
}

function handleSubmit(event, showLoading = false) {
    event.preventDefault();
    const form = event.target || document.getElementById('ingestForm');

    if (!form) {return;}

    // Declare resultsSection before use
    const resultsSection = document.querySelector('[data-results]');

    if (resultsSection) {
    // Show in-content loading spinner
        resultsSection.innerHTML = `
            <div class="relative mt-10">
                <div class="w-full h-full absolute inset-0 bg-black rounded-xl translate-y-2 translate-x-2"></div>
                <div class="bg-[#fafafa] rounded-xl border-[3px] border-gray-900 p-6 relative z-20 flex flex-col items-center space-y-4">
                    <div class="loader border-8 border-[#fff4da] border-t-8 border-t-[#ffc480] rounded-full w-16 h-16 animate-spin"></div>
                    <p class="text-lg font-bold text-gray-900">Loading...</p>
                </div>
            </div>
        `;
    }

    const submitButton = form.querySelector('button[type="submit"]');

    if (!submitButton) {return;}

    const formData = new FormData(form);

    // Update file size
    const slider = document.getElementById('file_size');

    if (slider) {
        formData.delete('max_file_size');
        formData.append('max_file_size', slider.value);
    }

    // Update pattern type and pattern
    const patternType = document.getElementById('pattern_type');
    const pattern = document.getElementById('pattern');

    if (patternType && pattern) {
        formData.delete('pattern_type');
        formData.delete('pattern');
        formData.append('pattern_type', patternType.value);
        formData.append('pattern', pattern.value);
    }

    // Ensure comment removal fields are directly updated from UI state
    const removeCommentsCheckbox = document.getElementById('removeComments');
    if (removeCommentsCheckbox) {
        formData.set('remove_comments', removeCommentsCheckbox.checked ? 'true' : 'false');
    }

    const commentCheckboxes = document.querySelectorAll('.comment-type-checkbox:checked');
    const selectedTypes = Array.from(commentCheckboxes).map(cb => cb.value);
    formData.set('comment_types', selectedTypes.join(','));

    // Log all form data before submission
    console.log('🚀 Form submission data:');
    for (const [key, value] of formData.entries()) {
        console.log(`  ${key}: ${value}`);
    }
    
    // Log checkbox states
    console.log('✅ Checkbox states:');
    console.log(`  removeComments checked: ${removeCommentsCheckbox?.checked || false}`);
    console.log(`  checked comment types: ${selectedTypes.join(',')}`);

    const originalContent = submitButton.innerHTML;

    if (showLoading) {
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <div class="flex items-center justify-center">
                <svg class="animate-spin h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="ml-2">Processing...</span>
            </div>
        `;
        submitButton.classList.add('bg-[#ffb14d]');
    }

    // Submit the form to /api/ingest
    fetch('/api/ingest', { method: 'POST', body: formData })
        .then((response) => response.json())
        .then((data) => {
            // Hide loading overlay
            if (resultsSection) {resultsSection.innerHTML = '';}
            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;

            if (!resultsSection) {return;}

            // Handle error
            if (data.error) {
                resultsSection.innerHTML = `<div class='mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700'>${data.error}</div>`;

                return;
            }

            // Build the static HTML structure
            resultsSection.innerHTML = `
                <div class="relative">
                    <div class="w-full h-full absolute inset-0 bg-gray-900 rounded-xl translate-y-2 translate-x-2"></div>
                    <div class="bg-[#fafafa] rounded-xl border-[3px] border-gray-900 p-6 relative z-20 space-y-6">
                        <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
                            <div class="md:col-span-5">
                                <div class="flex justify-between items-center mb-4 py-2">
                                    <h3 class="text-lg font-bold text-gray-900">Summary</h3>
                                </div>
                                <div class="relative">
                                    <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
                                    <textarea id="result-summary" class="w-full h-[160px] p-4 bg-[#fff4da] border-[3px] border-gray-900 rounded font-mono text-sm resize-none focus:outline-none relative z-10" readonly></textarea>
                                </div>
                                <div class="relative mt-4 inline-block group ml-4">
                                    <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
                                    <button onclick="copyFullDigest()" class="inline-flex items-center px-4 py-2 bg-[#ffc480] border-[3px] border-gray-900 text-gray-900 rounded group-hover:-translate-y-px group-hover:-translate-x-px transition-transform relative z-10">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                                        Copy all
                                    </button>
                                </div>
                                <div class="relative mt-4 inline-block group ml-4">
                                    <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
                                    <button onclick="downloadFullDigest()" class="inline-flex items-center px-4 py-2 bg-[#ffc480] border-[3px] border-gray-900 text-gray-900 rounded group-hover:-translate-y-px group-hover:-translate-x-px transition-transform relative z-10">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                        Download
                                    </button>
                                </div>
                            </div>
                            <div class="md:col-span-7">
                                <div class="flex justify-between items-center mb-4">
                                    <h3 class="text-lg font-bold text-gray-900">Directory Structure</h3>
                                    <div class="relative group">
                                        <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
                                        <button onclick="copyText('directory-structure')" class="px-4 py-2 bg-[#ffc480] border-[3px] border-gray-900 text-gray-900 rounded group-hover:-translate-y-px group-hover:-translate-x-px transition-transform relative z-10 flex items-center gap-2">
                                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                                            Copy
                                        </button>
                                    </div>
                                </div>
                                <div class="relative">
                                    <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
                                    <div class="directory-structure w-full p-4 bg-[#fff4da] border-[3px] border-gray-900 rounded font-mono text-sm resize-y focus:outline-none relative z-10 h-[215px] overflow-auto" id="directory-structure-container" readonly>
                                        <input type="hidden" id="directory-structure-content" value="" />
                                        <pre id="directory-structure-pre"></pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-4">
                                <h3 class="text-lg font-bold text-gray-900">Files Content</h3>
                                <div class="relative group">
                                    <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
                                    <button onclick="copyText('result-text')" class="px-4 py-2 bg-[#ffc480] border-[3px] border-gray-900 text-gray-900 rounded group-hover:-translate-y-px group-hover:-translate-x-px transition-transform relative z-10 flex items-center gap-2">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                                        Copy
                                    </button>
                                </div>
                            </div>
                            <div class="relative">
                                <div class="w-full h-full rounded bg-gray-900 translate-y-1 translate-x-1 absolute inset-0"></div>
                                <textarea id="result-content" class="result-text w-full p-4 bg-[#fff4da] border-[3px] border-gray-900 rounded font-mono text-sm resize-y focus:outline-none relative z-10" style="min-height: 600px" readonly></textarea>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Set plain text content for summary, tree, and content
            document.getElementById('result-summary').value = data.summary || '';
            document.getElementById('directory-structure-content').value = data.tree || '';
            document.getElementById('result-content').value = data.content || '';

            // Populate directory structure lines as clickable <pre> elements
            const dirPre = document.getElementById('directory-structure-pre');

            if (dirPre && data.tree) {
                dirPre.innerHTML = '';
                data.tree.split('\n').forEach((line) => {
                    const pre = document.createElement('pre');

                    pre.setAttribute('name', 'tree-line');
                    pre.className = 'cursor-pointer hover:line-through hover:text-gray-500';
                    pre.textContent = line;
                    pre.onclick = function () { toggleFile(this); };
                    dirPre.appendChild(pre);
                });
            }

            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        })
        .catch((error) => {
            // Hide loading overlay
            if (resultsSection) {
                resultsSection.innerHTML = '';
            }
            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;
            const errorContainer = document.querySelector('[data-results]');

            if (errorContainer) {
                errorContainer.innerHTML = `<div class='mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700'>${error}</div>`;
            }
        });
}

function copyFullDigest() {
    const directoryStructure = document.getElementById('directory-structure-content').value;
    const filesContent = document.querySelector('.result-text').value;
    const fullDigest = `${directoryStructure}\n\nFiles Content:\n\n${filesContent}`;
    const button = document.querySelector('[onclick="copyFullDigest()"]');
    const originalText = button.innerHTML;

    navigator.clipboard.writeText(fullDigest).then(() => {
        button.innerHTML = `
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Copied!
        `;

        setTimeout(() => {
            button.innerHTML = originalText;
        }, 2000);
    })
        .catch((err) => {
            console.error('Failed to copy text: ', err);
        });
}

function downloadFullDigest() {
    const summary = document.getElementById('result-summary').value;
    const directoryStructure = document.getElementById('directory-structure-content').value;
    const filesContent = document.querySelector('.result-text').value;

    // Create the full content with all three sections
    const fullContent = `${summary}\n${directoryStructure}\n${filesContent}`;

    // Create a blob with the content
    const blob = new Blob([fullContent], { type: 'text/plain' });

    // Create a download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = 'digest.txt';
    document.body.appendChild(a);
    a.click();

    // Clean up
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    // Show feedback on the button
    const button = document.querySelector('[onclick="downloadFullDigest()"]');
    const originalText = button.innerHTML;

    button.innerHTML = `
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        Downloaded!
    `;

    setTimeout(() => {
        button.innerHTML = originalText;
    }, 2000);
}

// Add the logSliderToSize helper function
function logSliderToSize(position) {
    const maxPosition = 500;
    const maxValue = Math.log(102400); // 100 MB

    const value = Math.exp(maxValue * (position / maxPosition)**1.5);

    return Math.round(value);
}

// Move slider initialization to a separate function
function initializeSlider() {
    const slider = document.getElementById('file_size');
    const sizeValue = document.getElementById('size_value');

    if (!slider || !sizeValue) {return;}

    function updateSlider() {
        const value = logSliderToSize(slider.value);

        sizeValue.textContent = formatSize(value);
        slider.style.backgroundSize = `${(slider.value / slider.max) * 100}% 100%`;
    }

    // Update on slider change
    slider.addEventListener('input', updateSlider);

    // Initialize slider position
    updateSlider();
}

// Add helper function for formatting size
function formatSize(sizeInKB) {
    if (sizeInKB >= 1024) {
        return `${ Math.round(sizeInKB / 1024) }MB`;
    }

    return `${ Math.round(sizeInKB) }kB`;
}

// Add this new function
function setupGlobalEnterHandler() {
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.target.matches('textarea')) {
            const form = document.getElementById('ingestForm');

            if (form) {
                handleSubmit(new Event('submit'), true);
            }
        }
    });
}

// Add to the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    initializeSlider();
    setupGlobalEnterHandler();
});


// Make sure these are available globally
window.handleSubmit = handleSubmit;
window.toggleFile = toggleFile;
window.copyText = copyText;
window.copyFullDigest = copyFullDigest;
window.downloadFullDigest = downloadFullDigest;
