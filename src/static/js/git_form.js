// Strike-through / un-strike file lines when the pattern-type menu flips.
function changePattern() {
    const files = document.getElementsByName('tree-line');

    files.forEach((el) => {
        if (el.textContent.includes('Directory structure:')) {return;}
        [
            'line-through',
            'text-gray-500',
            'hover:text-inherit',
            'hover:no-underline',
            'hover:line-through',
            'hover:text-gray-500',
        ].forEach((cls) => el.classList.toggle(cls));
    });
}

// Show/hide the Personal-Access-Token section when the “Private repository” checkbox is toggled.
function toggleAccessSettings() {
    const container = document.getElementById('accessSettingsContainer');
    const examples = document.getElementById('exampleRepositories');
    const show = document.getElementById('showAccessSettings')?.checked;

    container?.classList.toggle('hidden', !show);
    examples?.classList.toggle('lg:mt-0', show);
}

// Show/hide the comment types selector when the "Remove Comments" checkbox is toggled.
function toggleCommentRemoval() {
    const container = document.getElementById('commentTypesContainer');
    const checkbox = document.getElementById('removeComments');
    const show = checkbox?.checked;

    console.log('🔄 toggleCommentRemoval called:', {
        show,
        checkboxExists: !!checkbox,
        containerExists: !!container
    });

    container?.classList.toggle('hidden', !show);
    
    // Update hidden field
    const hiddenField = document.querySelector('input[name="remove_comments"]');
    if (hiddenField) {
        hiddenField.value = show ? 'true' : 'false';
        console.log('✅ Updated remove_comments hidden field:', hiddenField.value);
    } else {
        console.error('❌ Could not find remove_comments hidden field');
    }
    
    // Update comment types
    updateCommentTypes();
}

// Update comment types based on selected checkboxes
function updateCommentTypes() {
    const checkboxes = document.querySelectorAll('.comment-type-checkbox:checked');
    const selectedTypes = Array.from(checkboxes).map(cb => cb.value);
    
    console.log('🔄 updateCommentTypes called:', {
        checkboxCount: checkboxes.length,
        selectedTypes
    });
    
    // Update hidden field
    const hiddenField = document.querySelector('input[name="comment_types"]');
    if (hiddenField) {
        hiddenField.value = selectedTypes.join(',');
        console.log('✅ Updated comment_types hidden field:', hiddenField.value);
    } else {
        console.error('❌ Could not find comment_types hidden field');
    }
}

// Handle comment type checkbox changes
function handleCommentTypeChange(checkbox) {
    const allCheckbox = document.querySelector('.comment-type-checkbox[value="all"]');
    const otherCheckboxes = document.querySelectorAll('.comment-type-checkbox:not([value="all"])');
    
    console.log('🔄 handleCommentTypeChange called:', {
        changedValue: checkbox.value,
        changedChecked: checkbox.checked,
        allCheckboxExists: !!allCheckbox,
        otherCheckboxCount: otherCheckboxes.length
    });
    
    if (checkbox.value === 'all') {
        // If "all" is checked, uncheck others
        if (checkbox.checked) {
            otherCheckboxes.forEach(cb => cb.checked = false);
            console.log('✅ Unchecked all other checkboxes because "all" was selected');
        }
    } else {
        // If any other is checked, uncheck "all"
        if (checkbox.checked && allCheckbox) {
            allCheckbox.checked = false;
            console.log('✅ Unchecked "all" because specific type was selected');
        }
        // If no others are checked, check "all"
        const anyOtherChecked = Array.from(otherCheckboxes).some(cb => cb.checked);
        if (!anyOtherChecked && allCheckbox) {
            allCheckbox.checked = true;
            console.log('✅ Checked "all" because no specific types were selected');
        }
    }
    
    updateCommentTypes();
}



document.addEventListener('DOMContentLoaded', () => {
    document
        .getElementById('pattern_type')
        ?.addEventListener('change', () => changePattern());

    document
        .getElementById('showAccessSettings')
        ?.addEventListener('change', toggleAccessSettings);

    document
        .getElementById('removeComments')
        ?.addEventListener('change', toggleCommentRemoval);

    // Add event listeners to comment type checkboxes
    document.querySelectorAll('.comment-type-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', () => handleCommentTypeChange(checkbox));
    });

    // Initial UI sync
    toggleAccessSettings();
    toggleCommentRemoval();
    changePattern();
});


// Make them available to existing inline attributes
window.changePattern = changePattern;
window.toggleAccessSettings = toggleAccessSettings;
window.toggleCommentRemoval = toggleCommentRemoval;
window.updateCommentTypes = updateCommentTypes;
window.handleCommentTypeChange = handleCommentTypeChange;
