window.EmojiParticipant = (function () {

  let _name      = '';
  let _roll      = '';
  let _currentQ  = '';
  let _startTime = null;
  let _questions = {};
  let _submitted = {};
  let _submitLocked = false;

  function init() {
    if (window.HC_SESSION) {
      _name = window.HC_SESSION.name;
      _roll = window.HC_SESSION.roll;
    } else {
      const params = new URLSearchParams(window.location.search);
      _name = params.get('name') || 'Participant';
      _roll = params.get('roll') || 'Unknown';
    }

    document.getElementById('participant-badge').innerHTML = `
      <span>👤</span>
      <span class="badge-name">${escHtml(_name)}</span>
      <span class="badge-roll">${escHtml(_roll)}</span>
    `;

    document.getElementById('question-select').addEventListener('change', handleQuestionChange);
    document.getElementById('btn-submit').addEventListener('click', handleSubmit);

    loadQuestions();
  }

  async function loadQuestions() {
    try {
      const res  = await fetch(`${HC_CONFIG.BASE_URL}/questions?v=${Date.now()}`);
      _questions = await res.json();

      const select = document.getElementById('question-select');
      select.innerHTML = '<option value="">Select Question...</option>';

      Object.entries(_questions)
        .sort((a, b) => parseInt(a[0].replace('Q','')) - parseInt(b[0].replace('Q','')))
        .forEach(([qid, q]) => {
          const opt       = document.createElement('option');
          opt.value       = qid;
          opt.textContent = `${qid}: ${q.title}`;
          select.appendChild(opt);
        });

      buildProgressTracker();

      // ── Load previously solved from Supabase ──────────────────
      try {
        const solved = await HC_CONFIG.sbFetch(
          `solved_questions?team_name=eq.${encodeURIComponent(_name)}&select=question_id`
        );
        console.log('Solved from Supabase:', solved);
        if (solved && solved.length) {
          solved.forEach(s => {
            _submitted[s.question_id] = true;
            const opt = document.querySelector(`#question-select option[value="${s.question_id}"]`);
            if (opt) opt.textContent = `✅ ${s.question_id}: ${_questions[s.question_id]?.title || ''}`;
          });
          buildProgressTracker();
        }
      } catch(e) {
        console.error('Failed to fetch solved questions:', e);
      }

    } catch(e) {
      console.error('loadQuestions error:', e);
      window.EmojiUI.showToast('Failed to load questions', 'error');
    }
  }

  function buildProgressTracker() {
    const chipsEl  = document.getElementById('progress-chips');
    const totalEl  = document.getElementById('total-count');
    const solvedEl = document.getElementById('solved-count');
    if (!chipsEl) return;

    const qids = Object.keys(_questions)
      .sort((a,b) => parseInt(a.replace('Q','')) - parseInt(b.replace('Q','')));

    totalEl.textContent   = qids.length;
    solvedEl.textContent  = Object.keys(_submitted).length;
    chipsEl.innerHTML     = '';
    chipsEl.style.cssText = 'display:flex;gap:6px;flex-wrap:wrap;';

    qids.forEach(qid => {
      const chip     = document.createElement('span');
      chip.className = `progress-chip ${_submitted[qid] ? 'solved' : qid === _currentQ ? 'current' : 'pending'}`;
      chip.textContent = _submitted[qid] ? `${qid} ✓` : qid;
      chip.title       = _questions[qid]?.title || qid;
      chip.addEventListener('click', () => {
        document.getElementById('question-select').value = qid;
        handleQuestionChange();
      });
      chipsEl.appendChild(chip);
    });
  }

  function handleQuestionChange() {
    const qid         = document.getElementById('question-select').value;
    _currentQ         = qid;
    const submitBtn   = document.getElementById('btn-submit');
    const solvedBadge = document.getElementById('q-info-solved');

    submitBtn.disabled         = false;
    submitBtn.textContent      = '📤 Submit';
    submitBtn.style.background = '';
    submitBtn.style.opacity    = '';
    solvedBadge.classList.add('hidden');

    if (!qid) {
      document.getElementById('question-label').textContent = 'No question selected';
      document.getElementById('question-info-panel').classList.remove('visible');
      submitBtn.disabled = true;
      window.EmojiUI.showWelcome();
      buildProgressTracker();
      return;
    }

    _startTime = Date.now();
    const q    = _questions[qid];

    document.getElementById('question-label').textContent = `${qid}: ${q.title}`;
    document.getElementById('question-info-panel').classList.add('visible');
    document.getElementById('q-info-id').textContent    = qid;
    document.getElementById('q-info-title').textContent = q.title;
    document.getElementById('q-info-desc').textContent  = q.description;

    window.EmojiEditor.clear();
    window.EmojiEditor.setValue(
    `# Example Input/Output:
        
    # Read input
    n 📦 🔢➡️ ( 🎤 "" )
        
    # Print output
    📢 n
    `
    );
    const isSolved = !!_submitted[qid];

    if (isSolved) {
      submitBtn.disabled         = true;
      submitBtn.textContent      = '✅ Solved';
      submitBtn.style.background = 'var(--green)';
      submitBtn.style.opacity    = '0.8';
      solvedBadge.classList.remove('hidden');
      window.EmojiUI.showQuestionSolved(q, qid);
    } else {
      window.EmojiUI.showQuestionUnsolved(q, qid);
    }

    buildProgressTracker();
  }

  async function handleSubmit() {
    if (_submitLocked) return;
    _submitLocked = true;
    if (!_currentQ) { window.EmojiUI.showToast('Select a question first!', 'error'); return; }
    if (_submitted[_currentQ]) { window.EmojiUI.showToast('Already solved! Pick another.', 'info'); return; }

    const source = window.EmojiEditor.getValue().trim();
    if (!source) { window.EmojiUI.showToast('Write some code first!', 'error'); return; }

    // ── Frontend compile check (UX only, not security) ────────────────
    const { errors } = window.EmojiCompiler.compile(source);
    if (errors.length > 0) {
      window.EmojiUI.showCompileErrors(errors);
      window.EmojiUI.showToast('Fix compile errors first', 'error');
      return;
    }

    const submitBtn = document.getElementById('btn-submit');
    submitBtn.disabled    = true;
    window.EmojiUI.showSubmitting();
    let timeLeft = 7  ;
    submitBtn.textContent = `⏳ ${timeLeft}s`;

    const safetyTimer = setTimeout(() => {
      if (!_submitted[_currentQ]) {
        submitBtn.disabled    = false;
        submitBtn.textContent = '📤 Submit';
        submitBtn.style.background = '';
        window.EmojiUI.showToast('Submission timed out — try again', 'error');
      }
    }, 10000);

    try {
      // ── Step 1: Send emoji source to server for compilation ────────
      // Server compiles independently + signs with HMAC.
      // We never send our own compiled Python — server decides what runs.
      const compileRes = await fetch(`${HC_CONFIG.BASE_URL}/compile`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source }),
      });

      if (!compileRes.ok) throw new Error(`Compile HTTP ${compileRes.status}`);

      const compileData = await compileRes.json();

      if (!compileData.success) {
        // Stop animation immediately, show error in output panel
        clearTimeout(safetyTimer);
        submitBtn.disabled    = false;
        submitBtn.textContent = '📤 Submit';
        submitBtn.style.background = '';
        window.EmojiUI.showCompileErrors([{
          type:    'ValidationError',
          message: compileData.error || 'Raw Python not allowed',
          line:    1,
          hint:    'Use EmojiLang symbols only — check the docs panel for emoji equivalents.',
        }]);
        window.EmojiUI.showToast(compileData.error || 'Compile rejected', 'error');
        return;
      }

      // ── Step 2: Submit server's compiled Python + HMAC token ──────
      const res = await fetch(`${HC_CONFIG.BASE_URL}/submit`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name:      _name,
          roll:      _name,
          question:  _currentQ,
          code:      compileData.python,  // server's compiled output, not ours
          token:     compileData.token,   // HMAC signed by server secret
          startTime: _startTime,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const result = await res.json();

      if (!result.success) {
        window.EmojiUI.showToast(result.error || 'Submission failed', 'error');
        submitBtn.disabled    = false;
        submitBtn.textContent = '📤 Submit';
        submitBtn.style.background = '';
        return;
      }

      // Show test case results in output panel
      window.EmojiUI.showSubmitResult(result, _currentQ, _questions[_currentQ]);

      if (result.passed) {

        // ── Save to Supabase FIRST — confirm before updating UI ────
        try {
          const saveResult = await HC_CONFIG.sbFetch('solved_questions', 'POST', {
            team_name:   _name,
            question_id: _currentQ,
            time_taken:  result.timeTaken,
          });
          console.log('Saved to Supabase:', saveResult);

          // ── Confirmed saved — now mark in memory ──────────────────
          _submitted[_currentQ] = true;

          // ── Update submit button ──────────────────────────────────
          submitBtn.disabled         = true;
          submitBtn.textContent      = '✅ Solved';
          submitBtn.style.background = 'var(--green)';
          submitBtn.style.opacity    = '0.8';

          // ── Update solved badge ───────────────────────────────────
          document.getElementById('q-info-solved').classList.remove('hidden');

          // ── Update dropdown option ────────────────────────────────
          const opt = document.querySelector(`#question-select option[value="${_currentQ}"]`);
          if (opt) opt.textContent = `✅ ${_currentQ}: ${_questions[_currentQ].title}`;

          // ── Rebuild progress bar ──────────────────────────────────
          buildProgressTracker();

          window.EmojiUI.showToast(`✅ Correct! ${_currentQ} solved! 🎉`, 'success', 4000);

        } catch(e) {
          // Supabase failed — reset button so they can retry
          console.error('Failed to save to Supabase:', e);
          submitBtn.disabled    = false;
          submitBtn.textContent = '📤 Submit';
          submitBtn.style.background = '';
          window.EmojiUI.showToast(
            '⚠️ Answer correct but failed to save — please submit again!',
            'error',
            5000
          );
        }

      } else {
        // Wrong answer — reset button
        submitBtn.disabled    = false;
        submitBtn.textContent = '📤 Submit';
        submitBtn.style.background = '';
        window.EmojiUI.showToast('❌ Wrong answer — try again!', 'error', 3000);
      }

    } catch(e) {
      console.error('Submit error:', e);
      window.EmojiUI.showToast(`Submission failed: ${e.message}`, 'error');
      submitBtn.disabled    = false;
      submitBtn.textContent = '📤 Submit';
      submitBtn.style.background = '';
    } finally {
      clearTimeout(safetyTimer);
      _submitLocked = false;
    }
  }

  function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  return { init };

})();