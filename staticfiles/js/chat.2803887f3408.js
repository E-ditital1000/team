/*
 * Enhanced Chat.js - NextGen Creators Chat Module
 * A modernized chat implementation with improved UI/UX and functionality
 */

"use strict";

(function ($) {
  $.fn.chat = function (
    roomName,
    username,
    roomId,
    msg_counter_url = null,
    group = false
  ) {
    console.log("Chat initialized with:", {roomName, username, roomId, group});
    
    /*
     * ------------------------------------------------------------------------
     * Configuration and utilities
     * ------------------------------------------------------------------------
     */
    const config = {
      maxRetries: 5,
      retryInterval: 3000,
      typingTimeout: 1000,
      scrollThreshold: 30,
      maxImageSize: 5 * 1024 * 1024, // 5MB
      allowedImageTypes: ['image/jpeg', 'image/png', 'image/gif'],
      animationDuration: 300
    };
    
    // Notification functions
    function showNotification(message, type = 'info') {
      if (typeof toastr !== 'undefined') {
        switch(type) {
          case 'success': toastr.success(message); break;
          case 'error': toastr.error(message); break;
          case 'warning': toastr.warning(message); break;
          default: toastr.info(message);
        }
      } else {
        console.log(`[${type.toUpperCase()}]: ${message}`);
      }
    }
    
    function formatDate(dateString) {
      const date = new Date(dateString);
      const now = new Date();
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      
      // Format: Today/Yesterday at HH:MM AM/PM or MM/DD/YYYY at HH:MM AM/PM
      if (date.toDateString() === now.toDateString()) {
        return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } else if (date.toDateString() === yesterday.toDateString()) {
        return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } else {
        return date.toLocaleDateString([], { 
          month: 'short', 
          day: 'numeric', 
          year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined 
        }) + ` at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
    }
    
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    function linkify(text) {
      const urlRegex = /(https?:\/\/[^\s]+)/g;
      return text.replace(urlRegex, function(url) {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
      });
    }
    
    function autoGrowTextarea(element) {
      element.style.height = 'auto';
      element.style.height = element.scrollHeight + 'px';
    }
    
    /*
     * ------------------------------------------------------------------------
     * DOM Elements
     * ------------------------------------------------------------------------
     */
    const msgInput = document.getElementById('chat-message-input') || $('#chat-message-input')[0];
    const chatSubmit = document.getElementById('chat-message-submit') || $('#chat-message-submit')[0];
    const chatLog = document.getElementById('chat-log') || $('#chat-log')[0];
    const chatBody = document.querySelector('.chat-body') || $('.chat-body')[0];
    const loadMoreBtn = document.getElementById('load-more') || $('#load-more')[0];
    
    // Template for empty message placeholder
    const emptyMessage = `
      <div class="empty-msg text-center p-4">
        <div class="mb-3">
          <i class="fas fa-comments fa-3x text-muted"></i>
        </div>
        <h5>No messages yet</h5>
        <p class="text-muted">Start the conversation!</p>
      </div>`;
    
    // Template for history cleared message
    const historyCleared = `
      <div class="empty-msg text-center p-4">
        <div class="mb-3">
          <i class="fas fa-history fa-3x text-muted"></i>
        </div>
        <h5>Chat history was cleared</h5>
        <p class="text-muted">You can start a new conversation now.</p>
      </div>`;
    
    // Template for typing indicator
    const typingIndicator = `
      <div class="typing-indicator">
        <span class="typing-user">Someone</span> is typing
        <div class="typing-dots">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
        </div>
      </div>`;
    
    /*
     * ------------------------------------------------------------------------
     * Message templates
     * ------------------------------------------------------------------------
     */
    function createMessageHTML(msg) {
      const formattedDate = formatDate(msg.created);
      const messageId = `id_msg_${msg.id}`;
      const messageContent = linkify(escapeHtml(msg.content));
      
      if (group) {
        // Group chat message format
        if (msg.author === username) {
          // User's own message in group chat
          return `
            <li class="clearfix mb-3" id="${messageId}">
              <div class="message-container position-relative float-end">
                <div class="message-options">
                  <div class="dropdown">
                    <button class="btn btn-sm text-white" type="button" data-bs-toggle="dropdown">
                      <i class="fas fa-ellipsis-v"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                      <li><a class="dropdown-item copy-message" href="#"><i class="fas fa-copy me-2"></i>Copy</a></li>
                      <li><a class="dropdown-item delete-message" href="${msg.delete_url}" data-message-id="${msg.id}"><i class="fas fa-trash me-2"></i>Delete</a></li>
                    </ul>
                  </div>
                </div>
                <div class="message sent">
                  ${messageContent}
                </div>
                <div class="timestamp text-end">
                  ${formattedDate}
                </div>
              </div>
            </li>`;
        } else {
          // Other user's message in group chat
          return `
            <li class="mb-3" id="${messageId}">
              <div class="message-container position-relative">
                <div class="d-flex">
                  <div class="avatar avatar-sm me-2 bg-light rounded-circle d-flex align-items-center justify-content-center">
                    <span class="small">${msg.author.slice(0,1)}</span>
                  </div>
                  <div>
                    <div class="d-flex align-items-center">
                      <span class="fw-bold small">${msg.name || msg.author}</span>
                      <span class="text-muted ms-2 small">${formattedDate}</span>
                    </div>
                    <div class="message reply">
                      ${messageContent}
                    </div>
                  </div>
                </div>
              </div>
            </li>`;
        }
      } else {
        // Private chat message format
        if (msg.author === username) {
          // User's own message in private chat
          return `
            <li class="clearfix mb-3" id="${messageId}">
              <div class="message-container position-relative float-end">
                <div class="message-options">
                  <div class="dropdown">
                    <button class="btn btn-sm text-white" type="button" data-bs-toggle="dropdown">
                      <i class="fas fa-ellipsis-v"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                      <li><a class="dropdown-item copy-message" href="#"><i class="fas fa-copy me-2"></i>Copy</a></li>
                      <li><a class="dropdown-item delete-message" href="${msg.delete_url}" data-message-id="${msg.id}"><i class="fas fa-trash me-2"></i>Delete</a></li>
                    </ul>
                  </div>
                </div>
                <div class="message sent">
                  ${messageContent}
                </div>
                <div class="timestamp text-end">
                  ${formattedDate}
                </div>
              </div>
            </li>`;
        } else {
          // Other user's message in private chat
          return `
            <li class="mb-3" id="${messageId}">
              <div class="message-container position-relative">
                <div class="message reply">
                  ${messageContent}
                </div>
                <div class="timestamp">
                  ${formattedDate}
                </div>
              </div>
            </li>`;
        }
      }
    }
    
    /*
     * ------------------------------------------------------------------------
     * State management
     * ------------------------------------------------------------------------
     */
    let state = {
      next: 1,
      canFetchMore: true,
      isTyping: false,
      typingTimer: null,
      lastMessageTime: null,
      connectionAttempts: 0,
      isConnected: false
    };
    
    /*
     * ------------------------------------------------------------------------
     * WebSocket connection
     * ------------------------------------------------------------------------
     */
    const websocketUrl = (window.location.protocol === "https:" ? "wss://" : "ws://") + 
                         window.location.host + 
                         "/ws/chats/" + 
                         roomName + "/";
    
    console.log("WebSocket URL:", websocketUrl);
    const chatSocket = new ReconnectingWebSocket(websocketUrl);
    
    // WebSocket event handlers
    chatSocket.onopen = function(e) {
      console.log("WebSocket connection established");
      state.isConnected = true;
      state.connectionAttempts = 0;
      showNotification("Connected to chat", "success");
      fetchMessages(state.next);
    };
    
    chatSocket.onmessage = function(e) {
      const data = JSON.parse(e.data);
      console.log("WebSocket message received:", data.command);
      
      // Update next page information
      if (data.next_page === null) {
        console.log("All messages have been fetched");
        state.canFetchMore = false;
        if (loadMoreBtn) {
          $(loadMoreBtn).hide();
        }
      } else if (loadMoreBtn) {
        $(loadMoreBtn).show().text("Load older messages").attr("data-page", data.next_page);
      }
      
      // Handle different command types
      if (data.command === "messages") {
        handleMessagesResponse(data);
      } else if (data.command === "new_message") {
        handleNewMessage(data.message);
      } else if (data.command === "typing") {
        handleTypingIndicator(data.user);
      } else if (data.command === "read_receipt") {
        handleReadReceipt(data.message_id);
      }
      
      // Update unread message counters
      updateUnreadCounter();
    };
    
    chatSocket.onclose = function(e) {
      console.error("WebSocket connection closed");
      state.isConnected = false;
      state.connectionAttempts++;
      
      if (state.connectionAttempts <= config.maxRetries) {
        showNotification("Connection lost. Reconnecting...", "warning");
      } else {
        showNotification("Could not reconnect to chat. Please refresh the page.", "error");
      }
    };
    
    /*
     * ------------------------------------------------------------------------
     * Message handlers
     * ------------------------------------------------------------------------
     */
    function handleMessagesResponse(data) {
      // Check if the room has any messages
      if (data.messages.length === 0) {
        // Show appropriate placeholder based on whether history was cleared
        if (data.history_cleared) {
          $(chatLog).html(historyCleared);
        } else {
          $(chatLog).html(emptyMessage);
        }
        return;
      }
      
      // Remove any existing empty message placeholder
      $('.empty-msg').remove();
      
      // Process each message
      for (let i = 0; i < data.messages.length; i++) {
        createMessage(data.messages[i], "messages", data.auto_scroll);
      }
    }
    
    function handleNewMessage(message) {
      // Hide typing indicator if visible
      $('.typing-indicator').hide();
      
      // Create and add the message
      createMessage(message, "new_message", true);
      
      // Play notification sound if not from current user
      if (message.author !== username) {
        playMessageSound();
      }
    }
    
    function handleTypingIndicator(user) {
      if (user === username) return;
      
      // Show typing indicator with user's name
      let typingElement = $('.typing-indicator');
      
      if (typingElement.length === 0) {
        // Create typing indicator if it doesn't exist
        $(chatBody).append(typingIndicator);
        typingElement = $('.typing-indicator');
      }
      
      // Update the typing user name
      typingElement.find('.typing-user').text(user);
      typingElement.show();
      
      // Hide the indicator after a timeout
      setTimeout(() => {
        typingElement.fadeOut();
      }, 3000);
    }
    
    function handleReadReceipt(messageId) {
      // Add read receipt indicator to message
      $(`#id_msg_${messageId}`).find('.timestamp').append(' <i class="fas fa-check text-primary ms-1"></i>');
    }
    
    function createMessage(message, command, autoScroll = true) {
      // Generate HTML for the message
      const messageHTML = createMessageHTML(message);
      
      // Add message to chat log
      if (command === "new_message") {
        $(chatLog).append(messageHTML);
      } else {
        $(chatLog).prepend(messageHTML);
      }
      
      // Remove empty message indicator if it exists
      $('.empty-msg').remove();
      
      // Scroll to view new messages if needed
      if (autoScroll) {
        scrollToBottom();
      }
      
      // Update last message time
      state.lastMessageTime = new Date();
      
      // Initialize message interaction handlers
      initMessageInteractions();
    }
    
    function initMessageInteractions() {
      // Copy message handler
      $('.copy-message').off('click').on('click', function(e) {
        e.preventDefault();
        const messageText = $(this).closest('.message-container').find('.message').text().trim();
        
        navigator.clipboard.writeText(messageText)
          .then(() => {
            showNotification("Message copied to clipboard", "success");
          })
          .catch(err => {
            console.error('Failed to copy message:', err);
            showNotification("Failed to copy message", "error");
          });
      });
      
      // Delete message handler
      $('.delete-message').off('click').on('click', function(e) {
        e.preventDefault();
        const messageId = $(this).data('message-id');
        const deleteUrl = $(this).attr('href');
        
        if (confirm("Are you sure you want to delete this message?")) {
          $.ajax({
            url: deleteUrl,
            type: 'POST',
            headers: {
              'X-CSRFToken': getCSRFToken()
            },
            success: function(response) {
              if (response.deleted) {
                $(`#id_msg_${messageId}`).fadeOut(config.animationDuration, function() {
                  $(this).remove();
                });
                showNotification("Message deleted", "success");
              } else {
                showNotification("Could not delete message", "error");
              }
            },
            error: function() {
              showNotification("Error deleting message", "error");
            }
          });
        }
      });
    }
    
    function playMessageSound() {
      // Play a notification sound if available
      const sound = document.getElementById('message-sound');
      if (sound) {
        sound.play().catch(err => console.log('Could not play notification sound:', err));
      }
    }
    
    /*
     * ------------------------------------------------------------------------
     * Helper functions
     * ------------------------------------------------------------------------
     */
    function scrollToBottom() {
      if (chatBody) {
        $(chatBody).animate({ scrollTop: $(chatBody)[0].scrollHeight }, 200);
      } else {
        window.scrollTo(0, document.body.scrollHeight);
      }
    }
    
    function getCSRFToken() {
      let csrfToken = '';
      
      // Try to get from cookie
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
          csrfToken = cookie.substring('csrftoken='.length);
          break;
        }
      }
      
      // Fallback to meta tag
      if (!csrfToken) {
        const csrfEl = document.querySelector('meta[name="csrf-token"]');
        if (csrfEl) {
          csrfToken = csrfEl.getAttribute('content');
        }
      }
      
      return csrfToken;
    }
    
    function updateUnreadCounter() {
      if (!msg_counter_url) return;
      
      $.ajax({
        type: "GET",
        url: msg_counter_url,
        success: function(response) {
          if (response.total_unread_counter > 0) {
            $("#total-unread-msgs").text(response.total_unread_counter).show();
          } else {
            $("#total-unread-msgs").hide();
          }
        },
        error: function(error) {
          console.error("Error updating unread counter:", error);
        }
      });
    }
    
    function fetchMessages(page) {
      // Don't fetch if we've reached the end of messages
      if (!state.canFetchMore) return;
      
      // Don't refetch the same page
      if (page === state.next && page !== 1) return;
      
      console.log("Fetching messages, page:", page);
      
      chatSocket.send(JSON.stringify({
        roomId: roomId,
        command: "fetch_messages",
        page: page,
        username: username
      }));
      
      state.next = page;
    }
    
    function sendTypingIndicator() {
      // Don't send if not connected
      if (!state.isConnected) return;
      
      // Only send typing if not already sent recently
      if (!state.isTyping) {
        chatSocket.send(JSON.stringify({
          roomId: roomId,
          command: "typing",
          user: username
        }));
        
        state.isTyping = true;
        
        // Reset typing status after timeout
        clearTimeout(state.typingTimer);
        state.typingTimer = setTimeout(() => {
          state.isTyping = false;
        }, config.typingTimeout);
      }
    }
    
    /*
     * ------------------------------------------------------------------------
     * Event handlers
     * ------------------------------------------------------------------------
     */
    
    // Send message button click
    if (chatSubmit) {
      $(chatSubmit).on('click', function() {
        sendMessage();
      });
    }
    
    // Message input handling
    if (msgInput) {
      // Auto-resize textarea as user types
      $(msgInput).on('input', function() {
        autoGrowTextarea(this);
        
        // Enable/disable send button based on content
        if (chatSubmit) {
          if ($(this).val().trim() !== '') {
            $(chatSubmit).removeClass('disabled').prop('disabled', false);
          } else {
            $(chatSubmit).addClass('disabled').prop('disabled', true);
          }
        }
        
        // Send typing indicator
        sendTypingIndicator();
      });
      
      // Send on Enter key (not for group chats)
      $(msgInput).on('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey && !group) {
          e.preventDefault();
          sendMessage();
        }
      });
    }
    
    // Load more messages button
    if (loadMoreBtn) {
      $(loadMoreBtn).on('click', function() {
        const page = parseInt($(this).attr('data-page'));
        if (page) {
          fetchMessages(page);
        }
      });
    }
    
    // Scroll handler for infinite loading
    if (chatBody) {
      $(chatBody).on('scroll', function() {
        if ($(this).scrollTop() <= config.scrollThreshold) {
          fetchMessages(state.next + 1);
        }
      });
    }
    
    function sendMessage() {
      const message = $(msgInput).val().trim();
      if (message === '') return;
      
      // Send message via WebSocket
      chatSocket.send(JSON.stringify({
        roomId: roomId,
        command: "new_message",
        message: message,
        from: username
      }));
      
      // Clear input and focus
      $(msgInput).val('').focus();
      autoGrowTextarea(msgInput);
      
      // Disable button after sending
      if (chatSubmit) {
        $(chatSubmit).addClass('disabled').prop('disabled', true);
      }
      
      // Reset typing indicator state
      clearTimeout(state.typingTimer);
      state.isTyping = false;
    }
    
    /*
     * ------------------------------------------------------------------------
     * Initialization
     * ------------------------------------------------------------------------
     */
    function init() {
      // Set initial button state
      if (chatSubmit) {
        if (msgInput && $(msgInput).val().trim() !== '') {
          $(chatSubmit).removeClass('disabled').prop('disabled', false);
        } else {
          $(chatSubmit).addClass('disabled').prop('disabled', true);
        }
      }
      
      // Initialize textarea auto-resize
      if (msgInput) {
        autoGrowTextarea(msgInput);
      }
      
      // Initial unread counter update
      updateUnreadCounter();
    }
    
    // Run initialization
    init();
    
    // Return public API
    return {
      scrollToBottom,
      fetchMessages,
      updateUnreadCounter
    };
  };
})(jQuery);





// Add this to your JavaScript section in the template or as a separate file

document.addEventListener('DOMContentLoaded', function() {
  // Initialize emoji picker functionality
  const emojiBtn = document.getElementById('emoji-btn');
  const emojiPicker = document.getElementById('emoji-picker');
  const chatInput = document.getElementById('chat-message-input');
  
  if (emojiBtn && emojiPicker && chatInput) {
    // Toggle emoji picker visibility when the emoji button is clicked
    emojiBtn.addEventListener('click', function(e) {
      e.preventDefault(); // Prevent any default action
      
      if (emojiPicker.style.display === 'block') {
        emojiPicker.style.display = 'none';
      } else {
        emojiPicker.style.display = 'block';
        positionEmojiPicker();
      }
    });
    
    // Position the emoji picker relative to the button
    function positionEmojiPicker() {
      const buttonRect = emojiBtn.getBoundingClientRect();
      emojiPicker.style.left = buttonRect.left + 'px';
      emojiPicker.style.bottom = (window.innerHeight - buttonRect.top) + 'px';
    }
    
    // Add emoji to input when clicked
    document.querySelectorAll('.emoji-item').forEach(item => {
      item.addEventListener('click', function() {
        const emoji = this.getAttribute('data-emoji');
        
        // Insert emoji at cursor position
        const startPos = chatInput.selectionStart;
        const endPos = chatInput.selectionEnd;
        chatInput.value = chatInput.value.substring(0, startPos) + emoji + chatInput.value.substring(endPos);
        
        // Move cursor position after the inserted emoji
        chatInput.selectionStart = chatInput.selectionEnd = startPos + emoji.length;
        
        // Focus back on the input
        chatInput.focus();
        
        // Auto-grow the textarea
        chatInput.style.height = 'auto';
        chatInput.style.height = chatInput.scrollHeight + 'px';
        
        // Enable the send button
        document.getElementById('chat-message-submit').disabled = false;
        
        // Hide the emoji picker
        emojiPicker.style.display = 'none';
      });
    });
    
    // Close emoji picker when clicking outside
    document.addEventListener('click', function(e) {
      if (emojiPicker.style.display === 'block' && 
          !emojiBtn.contains(e.target) && 
          !emojiPicker.contains(e.target)) {
        emojiPicker.style.display = 'none';
      }
    });
    
    // Handle window resize to reposition the emoji picker if needed
    window.addEventListener('resize', function() {
      if (emojiPicker.style.display === 'block') {
        positionEmojiPicker();
      }
    });
  }
});




