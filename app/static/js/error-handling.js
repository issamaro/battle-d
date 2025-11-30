/**
 * Error Handling JavaScript
 * Battle-D Web App
 *
 * Interactive behaviors for flash messages, modals, and HTMX integration.
 */

// ========================================
// Flash Message Auto-Dismiss
// ========================================

/**
 * Auto-dismiss flash messages after a delay
 * @param {number} delay - Milliseconds before auto-dismiss (default: 5000)
 */
function initFlashMessages(delay = 5000) {
  const flashMessages = document.querySelectorAll('.flash-message');

  flashMessages.forEach((message) => {
    // Auto-dismiss after delay (except for errors)
    const category = message.getAttribute('data-category');
    if (category !== 'error') {
      setTimeout(() => {
        dismissFlashMessage(message);
      }, delay);
    }

    // Manual dismiss on close button click
    const closeBtn = message.querySelector('.flash-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        dismissFlashMessage(message);
      });
    }
  });
}

/**
 * Dismiss a flash message with animation
 * @param {HTMLElement} message - Flash message element to dismiss
 */
function dismissFlashMessage(message) {
  message.style.animation = 'slideOut 0.3s ease-out';

  message.addEventListener('animationend', () => {
    message.remove();
  });
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// ========================================
// Delete Modal Functions
// ========================================

/**
 * Open a delete confirmation modal
 * @param {string} modalId - ID of the modal dialog element
 */
function openDeleteModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal && modal.tagName === 'DIALOG') {
    modal.showModal();

    // Focus the cancel button for accessibility
    const cancelBtn = modal.querySelector('button.secondary');
    if (cancelBtn) {
      cancelBtn.focus();
    }
  }
}

/**
 * Close a delete confirmation modal
 * @param {string} modalId - ID of the modal dialog element
 */
function closeDeleteModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal && modal.tagName === 'DIALOG') {
    modal.close();
  }
}

/**
 * Initialize all delete modals on the page
 */
function initDeleteModals() {
  const modals = document.querySelectorAll('dialog[id^="delete-"]');

  modals.forEach((modal) => {
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.close();
      }
    });

    // Close on ESC key
    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        modal.close();
      }
    });
  });
}

// ========================================
// Form Validation Enhancement
// ========================================

/**
 * Enhance form field validation with live feedback
 */
function initFormValidation() {
  const forms = document.querySelectorAll('form[data-validate]');

  forms.forEach((form) => {
    const inputs = form.querySelectorAll('input, select, textarea');

    inputs.forEach((input) => {
      // Clear error state on input
      input.addEventListener('input', () => {
        if (input.getAttribute('aria-invalid') === 'true') {
          input.setAttribute('aria-invalid', 'false');

          // Hide associated error message
          const errorId = input.getAttribute('aria-describedby');
          if (errorId) {
            const errorElement = document.getElementById(errorId);
            if (errorElement) {
              errorElement.style.display = 'none';
            }
          }
        }
      });
    });
  });
}

// ========================================
// HTMX Integration
// ========================================

/**
 * Show loading indicator during HTMX requests
 */
function initHtmxLoading() {
  document.body.addEventListener('htmx:beforeRequest', (event) => {
    const indicator = event.detail.elt.querySelector('.htmx-indicator');
    if (indicator) {
      indicator.classList.add('htmx-request');
    }
  });

  document.body.addEventListener('htmx:afterRequest', (event) => {
    const indicator = event.detail.elt.querySelector('.htmx-indicator');
    if (indicator) {
      indicator.classList.remove('htmx-request');
    }
  });
}

/**
 * Handle HTMX errors with flash messages
 */
function initHtmxErrorHandling() {
  document.body.addEventListener('htmx:responseError', (event) => {
    const status = event.detail.xhr.status;
    let message = 'An error occurred. Please try again.';

    if (status === 404) {
      message = 'The requested resource was not found.';
    } else if (status === 500) {
      message = 'Server error. Please try again later.';
    } else if (status === 403) {
      message = 'You do not have permission to perform this action.';
    }

    // Create and show flash message
    showFlashMessage(message, 'error');
  });

  document.body.addEventListener('htmx:timeout', () => {
    showFlashMessage('Request timed out. Please check your connection.', 'warning');
  });
}

/**
 * Programmatically show a flash message
 * @param {string} message - Message text
 * @param {string} category - 'success', 'error', 'warning', or 'info'
 */
function showFlashMessage(message, category = 'info') {
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  const flashHTML = `
    <article class="flash-message flash-${category}" data-category="${category}" role="alert">
      <div class="flash-content">
        <span class="flash-icon" aria-hidden="true">${icons[category]}</span>
        <p>${message}</p>
      </div>
      <button class="flash-close" aria-label="Dismiss message" onclick="this.parentElement.remove()">×</button>
    </article>
  `;

  let container = document.querySelector('.flash-messages');
  if (!container) {
    container = document.createElement('div');
    container.className = 'flash-messages';
    container.setAttribute('role', 'status');
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'true');
    document.body.appendChild(container);
  }

  container.insertAdjacentHTML('beforeend', flashHTML);

  // Auto-dismiss after 5 seconds (except errors)
  if (category !== 'error') {
    const flashElement = container.lastElementChild;
    setTimeout(() => {
      dismissFlashMessage(flashElement);
    }, 5000);
  }
}

// ========================================
// Initialization
// ========================================

/**
 * Initialize all error handling features on page load
 */
function initErrorHandling() {
  initFlashMessages();
  initDeleteModals();
  initFormValidation();

  // Only initialize HTMX features if HTMX is loaded
  if (typeof htmx !== 'undefined') {
    initHtmxLoading();
    initHtmxErrorHandling();
  }
}

// Run on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initErrorHandling);
} else {
  initErrorHandling();
}

// Re-run on HTMX content swaps
document.body.addEventListener('htmx:afterSwap', () => {
  initFlashMessages();
  initDeleteModals();
  initFormValidation();
});

// Export functions for global use
window.openDeleteModal = openDeleteModal;
window.closeDeleteModal = closeDeleteModal;
window.showFlashMessage = showFlashMessage;
