// ==UserScript==
// @name         Telegram Message Extractor
// @match        https://web.telegram.org/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

(function () {
    'use strict';
  
        const tag = document.createElement('div');
    tag.textContent = 'tampermonkey: script is running';
    tag.style.cssText = `
      position: fixed; z-index: 999999;
      top: 10px; right: 10px;
      background: #000; color: #0f0;
      padding: 8px 10px; border-radius: 8px;
      font: 12px/1.2 monospace;
    `;
    document.documentElement.appendChild(tag);
    const seen = new WeakSet();
    const seenMessages = new WeakSet();
  
    function extractAvatarPeerId(group) {
      // avatar peer_id lives here
      const avatar = group.querySelector(
        '.bubbles-group-avatar-container [data-peer-id]'
      );
  
      if (!avatar) return;
  
      const peerId = avatar.getAttribute('data-peer-id');
      if (!peerId) return;
  
      // prevent duplicate logs for same DOM node
      if (seen.has(avatar)) return;
      seen.add(avatar);
  
      console.log('avatar peer_id:', peerId);
    }

    function extractMessageData(messageElement) {
      // prevent duplicate processing
      if (seenMessages.has(messageElement)) return;
      seenMessages.add(messageElement);

      const messageId = messageElement.getAttribute('data-message-id') || 
                        messageElement.id?.replace('message-', '');
      
      if (!messageId) return;

      // Find sender peer_id - try multiple locations
      let senderPeerId = null;
      
      // Method 1: Check if message has peer-id attribute
      senderPeerId = messageElement.getAttribute('data-peer-id');
      
      // Method 2: Look for avatar in parent message group
      if (!senderPeerId) {
        const messageGroup = messageElement.closest('[id^="message-group-"]');
        if (messageGroup) {
          const avatar = messageGroup.querySelector('[data-peer-id]');
          if (avatar) {
            senderPeerId = avatar.getAttribute('data-peer-id');
          }
        }
      }
      
      // Method 3: Look for peer-id in nearby elements
      if (!senderPeerId) {
        const peerElement = messageElement.querySelector('[data-peer-id]') ||
                           messageElement.parentElement?.querySelector('[data-peer-id]');
        if (peerElement) {
          senderPeerId = peerElement.getAttribute('data-peer-id');
        }
      }

      // Extract message content - try multiple selectors
      let content = '';
      
      // Try common Telegram Web message text selectors
      const textSelectors = [
        '.message-text',
        '.text-content',
        '[class*="text"]',
        '.bubble-content',
        '.message-content'
      ];
      
      for (const selector of textSelectors) {
        const textElement = messageElement.querySelector(selector);
        if (textElement) {
          content = textElement.textContent?.trim() || textElement.innerText?.trim() || '';
          if (content) break;
        }
      }
      
      // Fallback: get all text from message element, excluding nested interactive elements
      if (!content) {
        const clone = messageElement.cloneNode(true);
        // Remove buttons, links, and other interactive elements
        clone.querySelectorAll('button, a, [role="button"]').forEach(el => el.remove());
        content = clone.textContent?.trim() || clone.innerText?.trim() || '';
      }

      // Only log if we have meaningful data
      if (messageId) {
        const messageData = {
          messageId: messageId,
          senderPeerId: senderPeerId || 'unknown',
          content: content || '(no content)',
          timestamp: new Date().toISOString()
        };
        
        console.log('New message:', messageData);
        return messageData;
      }
      
      return null;
    }
  
    function start() {
      const observer = new MutationObserver(mutations => {
        for (const m of mutations) {
          for (const node of m.addedNodes) {
            if (!(node instanceof HTMLElement)) continue;
            
            // Check for bubbles-group (for peer_id extraction)
            if (node.classList?.contains('bubbles-group')) {
              extractAvatarPeerId(node);
            } else {
              const inner = node.querySelector?.('.bubbles-group');
              if (inner) extractAvatarPeerId(inner);
            }
            
            // Check for Message elements (for message content and sender)
            if (node.classList?.contains('Message') || 
                node.classList?.contains('message-list-item') ||
                node.id?.startsWith('message-')) {
              extractMessageData(node);
            } else {
              // Look for message elements inside the added node
              const messages = node.querySelectorAll?.('.Message, .message-list-item, [id^="message-"]');
              if (messages) {
                messages.forEach(msg => extractMessageData(msg));
              }
            }
          }
        }
      });
  
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  
    const wait = setInterval(() => {
      if (document.body) {
        clearInterval(wait);
        start();
      }
    }, 50);
  })();
  