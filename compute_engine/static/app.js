/**
 * Google Gemini Web Chatbot - Client Application
 * Supports: Gemini 3.8 Flash (Default) & Gemini 3.7 Flash
 */

(function () {
  'use strict';

  // Application State
  const state = {
    currentModel: 'gemini-3.8-flash',
    enableSearch: true, // Google Search Grounding 기본 활성화
    conversations: [],
    currentChatId: null,
    messages: [], // [{role: 'user'|'model', content: string, grounding?: object}]
    isGenerating: false,
    abortController: null,
    speechRecognition: null,
    isRecording: false
  };

  // DOM Elements
  const elements = {
    body: document.body,
    promptInput: document.getElementById('promptInput'),
    sendBtn: document.getElementById('sendBtn'),
    micBtn: document.getElementById('micBtn'),
    searchToggleBtn: document.getElementById('searchToggleBtn'),
    plusBtn: document.getElementById('plusBtn'),
    modelSelectBtn: document.getElementById('modelSelectBtn'),
    currentModelLabel: document.getElementById('currentModelLabel'),
    modelMenu: document.getElementById('modelMenu'),
    modelMenuItems: document.querySelectorAll('.model-menu-item'),
    messagesStream: document.getElementById('messagesStream'),
    chatContainer: document.getElementById('chatContainer'),
    heroSection: document.getElementById('heroSection'),
    newChatBtn: document.getElementById('newChatBtn'),
    clearAllChatsBtn: document.getElementById('clearAllChatsBtn'),
    chatHistoryList: document.getElementById('chatHistoryList'),
    sidebar: document.getElementById('sidebar'),
    sidebarToggleBtn: document.getElementById('sidebarToggleBtn'),
    sidebarCloseBtn: document.getElementById('sidebarCloseBtn'),
    sidebarModelText: document.getElementById('sidebarModelText'),
    themeToggleBtn: document.getElementById('themeToggleBtn'),
    themeIconSun: document.getElementById('themeIconSun'),
    themeIconMoon: document.getElementById('themeIconMoon'),
    quickPromptsModal: document.getElementById('quickPromptsModal'),
    apiStatusTag: document.getElementById('apiStatusTag'),
    inputPillWrapper: document.getElementById('inputPillWrapper')
  };

  // Configure Marked.js
  if (window.marked) {
    marked.setOptions({
      breaks: true,
      gfm: true
    });
  }

  // Model Metadata
  const MODEL_METADATA = {
    'gemini-3.8-flash': {
      name: 'Gemini 3.8 Flash',
      label: 'Flash',
      badge: 'Flash 3.8 (최신)'
    },
    'gemini-3.7-flash': {
      name: 'Gemini 3.7 Flash',
      label: 'Flash 3.7',
      badge: 'Flash 3.7'
    }
  };

  /* ==========================================================================
     Initialization
     ========================================================================== */
  function init() {
    loadSavedSettings();
    loadSavedConversations();
    setupEventListeners();
    setupSpeechRecognition();
    checkApiStatus();
  }

  function loadSavedSettings() {
    // Restore Theme
    const savedTheme = localStorage.getItem('gemini_theme') || 'light';
    applyTheme(savedTheme);

    // Restore Model
    const savedModel = localStorage.getItem('gemini_model');
    if (savedModel && MODEL_METADATA[savedModel]) {
      setModel(savedModel);
    } else {
      setModel('gemini-3.8-flash');
    }

    // Restore Search Grounding Preference (기본값: true)
    const savedSearch = localStorage.getItem('gemini_enable_search');
    state.enableSearch = savedSearch !== 'false';
    updateSearchToggleUI();
  }

  /* ==========================================================================
     Real-Time Search Grounding Toggle
     ========================================================================== */
  function toggleSearch() {
    state.enableSearch = !state.enableSearch;
    localStorage.setItem('gemini_enable_search', state.enableSearch);
    updateSearchToggleUI();
  }

  function updateSearchToggleUI() {
    if (!elements.searchToggleBtn) return;
    if (state.enableSearch) {
      elements.searchToggleBtn.classList.add('active');
      elements.searchToggleBtn.title = '실시간 웹 검색 (Google Search) 켜짐';
    } else {
      elements.searchToggleBtn.classList.remove('active');
      elements.searchToggleBtn.title = '실시간 웹 검색 꺼짐 (클릭하여 켜기)';
    }
  }

  /* ==========================================================================
     Theme Management
     ========================================================================== */
  function applyTheme(theme) {
    if (theme === 'dark') {
      elements.body.classList.remove('light-theme');
      elements.body.classList.add('dark-theme');
      elements.themeIconSun.classList.add('hidden');
      elements.themeIconMoon.classList.remove('hidden');
    } else {
      elements.body.classList.remove('dark-theme');
      elements.body.classList.add('light-theme');
      elements.themeIconSun.classList.remove('hidden');
      elements.themeIconMoon.classList.add('hidden');
    }
    localStorage.setItem('gemini_theme', theme);
  }

  function toggleTheme() {
    const isDark = elements.body.classList.contains('dark-theme');
    applyTheme(isDark ? 'light' : 'dark');
  }

  /* ==========================================================================
     Model Selection
     ========================================================================== */
  function setModel(modelId) {
    if (!MODEL_METADATA[modelId]) return;
    state.currentModel = modelId;
    localStorage.setItem('gemini_model', modelId);

    // Update UI labels
    elements.currentModelLabel.textContent = MODEL_METADATA[modelId].label;
    if (elements.sidebarModelText) {
      elements.sidebarModelText.textContent = MODEL_METADATA[modelId].name;
    }

    // Update Menu active states
    elements.modelMenuItems.forEach(item => {
      if (item.dataset.model === modelId) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    closeModelMenu();
  }

  function toggleModelMenu() {
    const isOpen = elements.modelMenu.classList.contains('show');
    if (isOpen) {
      closeModelMenu();
    } else {
      elements.modelMenu.classList.add('show');
      elements.modelSelectBtn.setAttribute('aria-expanded', 'true');
    }
  }

  function closeModelMenu() {
    elements.modelMenu.classList.remove('show');
    elements.modelSelectBtn.setAttribute('aria-expanded', 'false');
  }

  /* ==========================================================================
     Health & API Status Check
     ========================================================================== */
  async function checkApiStatus() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        const tag = elements.apiStatusTag;
        if (data.apiKeyConfigured) {
          tag.querySelector('.status-indicator').className = 'status-indicator online';
          tag.querySelector('.status-label').textContent = 'API 연결됨';
        } else {
          tag.querySelector('.status-indicator').className = 'status-indicator offline';
          tag.querySelector('.status-label').textContent = 'API 키 누락';
        }
      }
    } catch (e) {
      console.warn('API status check failed:', e);
    }
  }

  /* ==========================================================================
     Speech Recognition (Web Speech API)
     ========================================================================== */
  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      elements.micBtn.title = '이 브라우저는 음성 인식을 지원하지 않습니다.';
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'ko-KR';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      state.isRecording = true;
      elements.micBtn.classList.add('recording');
      elements.micBtn.title = '듣고 있습니다... 말씀해주세요';
    };

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      elements.promptInput.value = transcript;
      handleInputResize();
      updateSendButtonState();
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      stopRecording();
    };

    recognition.onend = () => {
      stopRecording();
    };

    state.speechRecognition = recognition;
  }

  function toggleSpeechRecording() {
    if (!state.speechRecognition) {
      alert('사용 중인 브라우저에서 마이크 음성 인식을 지원하지 않습니다.');
      return;
    }

    if (state.isRecording) {
      state.speechRecognition.stop();
      stopRecording();
    } else {
      try {
        state.speechRecognition.start();
      } catch (err) {
        console.error('Speech start error:', err);
      }
    }
  }

  function stopRecording() {
    state.isRecording = false;
    elements.micBtn.classList.remove('recording');
    elements.micBtn.title = '음성으로 입력하기';
  }

  /* ==========================================================================
     Chat & Streaming Execution
     ========================================================================== */
  function updateSendButtonState() {
    if (state.isGenerating) {
      elements.sendBtn.disabled = false;
      elements.sendBtn.classList.add('generating');
      elements.sendBtn.title = '답변 생성 중단';
      elements.sendBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <rect x="6" y="6" width="12" height="12" rx="2"></rect>
        </svg>
      `;
    } else {
      elements.sendBtn.classList.remove('generating');
      elements.sendBtn.title = '메시지 전송';
      elements.sendBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5"></line>
          <polyline points="5 12 12 5 19 12"></polyline>
        </svg>
      `;
      const hasContent = elements.promptInput.value.trim().length > 0;
      elements.sendBtn.disabled = !hasContent;
    }
  }

  function handleInputResize() {
    const textarea = elements.promptInput;
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 160);
    textarea.style.height = newHeight + 'px';

    if (newHeight > 40) {
      elements.inputPillWrapper.classList.add('multi-line');
    } else {
      elements.inputPillWrapper.classList.remove('multi-line');
    }
  }

  async function handleSendMessage() {
    if (state.isGenerating) {
      // User clicked stop button
      if (state.abortController) {
        state.abortController.abort();
      }
      return;
    }

    const text = elements.promptInput.value.trim();
    if (!text) return;

    // Reset input
    elements.promptInput.value = '';
    handleInputResize();
    updateSendButtonState();
    closeQuickPrompts();

    // Activate chat view
    elements.body.classList.add('chat-active');

    // Add user message to state & UI
    const userMsg = { role: 'user', content: text };
    state.messages.push(userMsg);
    appendUserMessage(text);

    // Save conversation title if new
    if (!state.currentChatId) {
      state.currentChatId = 'chat_' + Date.now();
      const title = text.slice(0, 30) + (text.length > 30 ? '...' : '');
      state.conversations.unshift({
        id: state.currentChatId,
        title: title,
        timestamp: Date.now()
      });
      renderChatHistoryList();
    }

    // Prepare Gemini placeholder row
    const geminiRow = createGeminiMessageRow();
    elements.messagesStream.appendChild(geminiRow);
    scrollToBottom();

    // Streaming State
    state.isGenerating = true;
    state.abortController = new AbortController();
    updateSendButtonState();

    let fullAnswer = '';
    let groundingData = null;
    const contentTarget = geminiRow.querySelector('.gemini-text');
    const modelUsed = state.currentModel;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: modelUsed,
          messages: state.messages,
          enable_search: state.enableSearch
        }),
        signal: state.abortController.signal
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `서버 오류 (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep last incomplete line

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const jsonStr = trimmed.slice(5).trim();
            if (!jsonStr) continue;

            try {
              const data = JSON.parse(jsonStr);
              if (data.error) {
                throw new Error(data.error);
              }
              if (data.text) {
                fullAnswer += data.text;
                renderMarkdown(contentTarget, fullAnswer, true);
                scrollToBottom();
              }
              if (data.grounding) {
                groundingData = data.grounding;
              }
              if (data.done) {
                break;
              }
            } catch (e) {
              console.error('SSE parse error:', e, jsonStr);
            }
          }
        }
      }

    } catch (err) {
      if (err.name === 'AbortError') {
        fullAnswer += '\n\n*(생성이 사용자에 의해 중단되었습니다)*';
      } else {
        fullAnswer += `\n\n> ⚠️ **오류 발생**: ${err.message}`;
      }
    } finally {
      state.isGenerating = false;
      state.abortController = null;
      updateSendButtonState();

      // Final rendering without cursor
      renderMarkdown(contentTarget, fullAnswer, false);
      
      // Render grounding box if search was used
      if (groundingData && ((groundingData.search_queries && groundingData.search_queries.length > 0) || (groundingData.sources && groundingData.sources.length > 0))) {
        appendGroundingBox(geminiRow, groundingData);
      }

      state.messages.push({ role: 'model', content: fullAnswer, grounding: groundingData });
      saveConversationMessages();

      // Append action buttons (Copy, Regenerate, Model tag)
      appendMessageActions(geminiRow, fullAnswer, modelUsed);
      scrollToBottom();
    }
  }

  /* ==========================================================================
     DOM Construction for Messages
     ========================================================================== */
  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row user-row';

    const bubble = document.createElement('div');
    bubble.className = 'user-bubble';
    bubble.textContent = text;

    row.appendChild(bubble);
    elements.messagesStream.appendChild(row);
  }

  function createGeminiMessageRow() {
    const row = document.createElement('div');
    row.className = 'message-row gemini-row';

    row.innerHTML = `
      <div class="gemini-avatar">
        <svg class="gemini-star-logo" viewBox="0 0 28 28" width="28" height="28">
          <path fill="url(#geminiGrad)" d="M14,0 C14,7.732 7.732,14 0,14 C7.732,14 14,20.268 14,28 C14,20.268 20.268,14 28,14 C20.268,14 14,7.732 14,0 Z"/>
        </svg>
      </div>
      <div class="gemini-content-wrapper">
        <div class="gemini-text">
          <span class="typing-cursor"></span>
        </div>
      </div>
    `;

    return row;
  }

  function renderMarkdown(container, rawMarkdown, isStreaming) {
    if (window.marked) {
      let parsed = marked.parse(rawMarkdown || '');
      if (isStreaming) {
        parsed += '<span class="typing-cursor"></span>';
      }
      container.innerHTML = parsed;
    } else {
      container.textContent = rawMarkdown;
      if (isStreaming) {
        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        container.appendChild(cursor);
      }
    }

    // Enhance Code Blocks
    enhanceCodeBlocks(container);
  }

  function enhanceCodeBlocks(container) {
    const codeBlocks = container.querySelectorAll('pre code');
    codeBlocks.forEach(code => {
      // Highlight syntax if library available
      if (window.hljs && !code.dataset.highlighted) {
        hljs.highlightElement(code);
      }

      const pre = code.parentElement;
      if (pre.parentElement && pre.parentElement.classList.contains('code-block-wrapper')) {
        return;
      }

      // Create code wrapper
      const wrapper = document.createElement('div');
      wrapper.className = 'code-block-wrapper';

      // Detect language
      let lang = 'code';
      code.classList.forEach(cls => {
        if (cls.startsWith('language-')) {
          lang = cls.replace('language-', '');
        }
      });

      const header = document.createElement('div');
      header.className = 'code-header';
      header.innerHTML = `
        <span>${lang}</span>
        <button class="code-copy-btn" type="button" title="코드 복사">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>복사</span>
        </button>
      `;

      const copyBtn = header.querySelector('.code-copy-btn');
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(code.innerText).then(() => {
          copyBtn.innerHTML = `
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#34a853" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span style="color:#34a853;">복사됨</span>
          `;
          setTimeout(() => {
            copyBtn.innerHTML = `
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>복사</span>
            `;
          }, 2000);
        });
      });

      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(header);
      wrapper.appendChild(pre);
    });
  }

  function appendMessageActions(row, content, modelId) {
    const wrapper = row.querySelector('.gemini-content-wrapper');
    if (wrapper.querySelector('.gemini-actions')) return;

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'gemini-actions';

    const modelName = MODEL_METADATA[modelId] ? MODEL_METADATA[modelId].badge : modelId;

    actionsDiv.innerHTML = `
      <span class="model-tag">${modelName}</span>
      <button class="action-text-btn copy-btn" title="전체 답변 복사">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span>복사</span>
      </button>
      <button class="action-text-btn regen-btn" title="답변 다시 생성">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"></polyline>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>
        <span>다시 생성</span>
      </button>
    `;

    // Copy Action
    const copyBtn = actionsDiv.querySelector('.copy-btn');
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(content).then(() => {
        copyBtn.querySelector('span').textContent = '복사됨';
        setTimeout(() => {
          copyBtn.querySelector('span').textContent = '복사';
        }, 1800);
      });
    });

    // Regenerate Action
    const regenBtn = actionsDiv.querySelector('.regen-btn');
    regenBtn.addEventListener('click', () => {
      if (state.isGenerating) return;
      // Remove last model message
      state.messages.pop();
      row.remove();
      // Resend
      const lastUserMsg = state.messages[state.messages.length - 1];
      if (lastUserMsg && lastUserMsg.role === 'user') {
        // Pop user message as well because handleSendMessage re-appends it
        state.messages.pop();
        elements.promptInput.value = lastUserMsg.content;
        handleSendMessage();
      }
    });

    wrapper.appendChild(actionsDiv);
  }

  /* ==========================================================================
     Real-Time Search Grounding Rendering
     ========================================================================== */
  function appendGroundingBox(row, grounding) {
    if (!grounding) return;
    const wrapper = row.querySelector('.gemini-content-wrapper');
    if (!wrapper || wrapper.querySelector('.grounding-box')) return;

    const box = document.createElement('div');
    box.className = 'grounding-box';

    let innerHtml = `
      <div class="grounding-header">
        <svg class="grounding-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="2" y1="12" x2="22" y2="12"></line>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
        </svg>
        <span>실시간 Google 검색 참조</span>
      </div>
    `;

    if (grounding.search_queries && grounding.search_queries.length > 0) {
      innerHtml += '<div class="search-queries-list">';
      grounding.search_queries.forEach(q => {
        innerHtml += `<span class="search-query-badge">🔍 ${escapeHtml(q)}</span>`;
      });
      innerHtml += '</div>';
    }

    if (grounding.sources && grounding.sources.length > 0) {
      innerHtml += '<div class="sources-header">웹 출처</div><div class="sources-grid">';
      grounding.sources.forEach(src => {
        innerHtml += `
          <a class="source-card" href="${escapeHtml(src.uri)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(src.title)}">
            <svg class="source-card-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
            <span class="source-card-title">${escapeHtml(src.title)}</span>
          </a>
        `;
      });
      innerHtml += '</div>';
    }

    box.innerHTML = innerHtml;

    // Insert before actions if present
    const actions = wrapper.querySelector('.gemini-actions');
    if (actions) {
      wrapper.insertBefore(box, actions);
    } else {
      wrapper.appendChild(box);
    }
  }

  function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
  }

  /* ==========================================================================
     Conversation History Management
     ========================================================================== */
  function loadSavedConversations() {
    try {
      const stored = localStorage.getItem('gemini_chat_history');
      if (stored) {
        state.conversations = JSON.parse(stored);
        renderChatHistoryList();
      }
    } catch (e) {
      console.warn('Failed to load chat history:', e);
    }
  }

  function saveConversationsToStorage() {
    try {
      localStorage.setItem('gemini_chat_history', JSON.stringify(state.conversations));
    } catch (e) {
      console.warn('Failed to save chat history:', e);
    }
  }

  function saveConversationMessages() {
    if (!state.currentChatId) return;
    try {
      localStorage.setItem(`gemini_msg_${state.currentChatId}`, JSON.stringify(state.messages));
      saveConversationsToStorage();
    } catch (e) {
      console.warn('Failed to save message items:', e);
    }
  }

  function renderChatHistoryList() {
    elements.chatHistoryList.innerHTML = '';
    if (state.conversations.length === 0) {
      elements.chatHistoryList.innerHTML = `
        <div style="padding: 12px 14px; font-size: 13px; color: var(--text-hint);">
          대화 기록이 없습니다.
        </div>
      `;
      return;
    }

    state.conversations.forEach(chat => {
      const item = document.createElement('div');
      item.className = 'chat-history-item';
      if (chat.id === state.currentChatId) {
        item.classList.add('active');
      }

      item.innerHTML = `
        <span class="history-item-title">${escapeHtml(chat.title)}</span>
        <button class="delete-chat-btn" title="삭제">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      `;

      item.addEventListener('click', (e) => {
        if (e.target.closest('.delete-chat-btn')) {
          deleteConversation(chat.id);
          return;
        }
        loadConversation(chat.id);
      });

      elements.chatHistoryList.appendChild(item);
    });
  }

  function loadConversation(chatId) {
    if (state.isGenerating) return;
    state.currentChatId = chatId;
    elements.body.classList.add('chat-active');
    elements.messagesStream.innerHTML = '';

    try {
      const saved = localStorage.getItem(`gemini_msg_${chatId}`);
      if (saved) {
        state.messages = JSON.parse(saved);
        state.messages.forEach(msg => {
          if (msg.role === 'user') {
            appendUserMessage(msg.content);
          } else {
            const row = createGeminiMessageRow();
            elements.messagesStream.appendChild(row);
            renderMarkdown(row.querySelector('.gemini-text'), msg.content, false);
            if (msg.grounding) {
              appendGroundingBox(row, msg.grounding);
            }
            appendMessageActions(row, msg.content, state.currentModel);
          }
        });
        scrollToBottom();
      }
    } catch (e) {
      console.warn('Failed to load conversation messages:', e);
    }

    renderChatHistoryList();
    closeSidebar();
  }

  function deleteConversation(chatId) {
    state.conversations = state.conversations.filter(c => c.id !== chatId);
    localStorage.removeItem(`gemini_msg_${chatId}`);
    saveConversationsToStorage();

    if (state.currentChatId === chatId) {
      startNewChat();
    } else {
      renderChatHistoryList();
    }
  }

  function startNewChat() {
    if (state.isGenerating && state.abortController) {
      state.abortController.abort();
    }
    state.currentChatId = null;
    state.messages = [];
    elements.messagesStream.innerHTML = '';
    elements.promptInput.value = '';
    handleInputResize();
    updateSendButtonState();
    elements.body.classList.remove('chat-active');
    renderChatHistoryList();
    closeSidebar();
  }

  function clearAllConversations() {
    if (confirm('모든 대화 기록을 삭제하시겠습니까?')) {
      state.conversations.forEach(c => localStorage.removeItem(`gemini_msg_${c.id}`));
      state.conversations = [];
      saveConversationsToStorage();
      startNewChat();
    }
  }

  /* ==========================================================================
     Sidebar & Modals
     ========================================================================== */
  function toggleSidebar() {
    elements.sidebar.classList.toggle('open');
  }

  function closeSidebar() {
    elements.sidebar.classList.remove('open');
  }

  function toggleQuickPrompts() {
    elements.quickPromptsModal.classList.toggle('show');
  }

  function closeQuickPrompts() {
    elements.quickPromptsModal.classList.remove('show');
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /* ==========================================================================
     Event Listeners
     ========================================================================== */
  function setupEventListeners() {
    // Prompt Input Events
    elements.promptInput.addEventListener('input', () => {
      handleInputResize();
      updateSendButtonState();
    });

    elements.promptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    // Send Button
    elements.sendBtn.addEventListener('click', handleSendMessage);

    // Mic Button
    elements.micBtn.addEventListener('click', toggleSpeechRecording);

    // Search Toggle Button (Google Search Grounding)
    if (elements.searchToggleBtn) {
      elements.searchToggleBtn.addEventListener('click', toggleSearch);
    }

    // Plus Button (Quick Prompts)
    elements.plusBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleQuickPrompts();
    });

    // Quick Prompts Selection
    document.querySelectorAll('.prompt-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        elements.promptInput.value = chip.dataset.prompt;
        handleInputResize();
        updateSendButtonState();
        closeQuickPrompts();
        elements.promptInput.focus();
      });
    });

    // Model Selector Toggle
    elements.modelSelectBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleModelMenu();
    });

    // Model Items Click
    elements.modelMenuItems.forEach(item => {
      item.addEventListener('click', () => {
        const modelId = item.dataset.model;
        setModel(modelId);
      });
    });

    // Close Dropdowns on outside click
    document.addEventListener('click', (e) => {
      if (!elements.modelDropdownContainer.contains(e.target)) {
        closeModelMenu();
      }
      if (!elements.quickPromptsModal.contains(e.target) && e.target !== elements.plusBtn) {
        closeQuickPrompts();
      }
    });

    // New Chat Button
    elements.newChatBtn.addEventListener('click', startNewChat);

    // Clear History Button
    elements.clearAllChatsBtn.addEventListener('click', clearAllConversations);

    // Sidebar Toggle
    elements.sidebarToggleBtn.addEventListener('click', toggleSidebar);
    elements.sidebarCloseBtn.addEventListener('click', closeSidebar);

    // Theme Toggle
    elements.themeToggleBtn.addEventListener('click', toggleTheme);

    // Window Resize
    window.addEventListener('resize', handleInputResize);
  }

  // Run on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
