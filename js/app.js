// /**
//  * app.js
//  * Main entry point. Wires together all modules.
//  */

// (function () {

//   document.addEventListener('DOMContentLoaded', () => {
//     window.EmojiEditor.init();
//     window.EmojiSidebar.init();
//     window.EmojiUI.init();
//     window.EmojiParticipant.init();

//     bindButtons();
//     bindTabs();
//   });

//   function bindButtons() {
//     document.getElementById('btn-run').addEventListener('click', runCode);
//     document.getElementById('btn-clear').addEventListener('click', clearEditor);
//     document.getElementById('btn-example').addEventListener('click', showExamplePicker);
//   }

//   function bindTabs() {
//     document.querySelectorAll('.tab').forEach(tab => {
//       tab.addEventListener('click', () => {
//         const target = tab.dataset.tab;
//         document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
//         tab.classList.add('active');
//         window.EmojiUI.toggleDocs(target === 'docs');
//       });
//     });
//   }

//   async function runCode() {
//     const source = window.EmojiEditor.getValue().trim();
//     if (!source) { window.EmojiUI.showToast('Write some emoji code first! 🖊️', 'error'); return; }

//     const { python, errors } = window.EmojiCompiler.compile(source);
//     if (errors.length > 0) {
//       window.EmojiUI.showCompileErrors(errors);
//       window.EmojiUI.showToast(`${errors.length} compile error${errors.length > 1 ? 's' : ''} found`, 'error');
//       return;
//     }

//     const runBtn = document.getElementById('btn-run');
//     runBtn.disabled = true;
//     window.EmojiUI.showRunning();

//     try {
//       // const result = await window.EmojiRunner.run(python);
//       const result = await window.EmojiRunner.run(python, currentQuestionId);
//       if (result.exitCode === 0 && !result.error) {
//         window.EmojiUI.showSuccess(result);
//         window.EmojiUI.showToast('Ran successfully ✓', 'success');
//       } else {
//         window.EmojiUI.showRuntimeError(result);
//         window.EmojiUI.showToast('Runtime error 💥', 'error');
//       }
//     } catch (err) {
//       window.EmojiUI.showFatalError(err.message || 'Unknown error');
//       window.EmojiUI.showToast('API error', 'error');
//     } finally {
//       runBtn.disabled = false;
//     }
//   }

//   function clearEditor() {
//     if (!window.EmojiEditor.getValue().trim()) return;
//     if (confirm('Clear the editor?')) {
//       window.EmojiEditor.clear();
//       window.EmojiUI.showWelcome();
//       window.EmojiUI.showToast('Editor cleared', 'info');
//     }
//   }

//   function showExamplePicker() {
//     const examples = window.EMOJI_LANG.examples;
//     const labels = {
//       helloWorld: '👋 Hello World',
//       variables:  '📦 Variables',
//       ifElse:     '🤔 If / Else',
//       loop:       '🔁 Loops',
//       function:   '🔧 Functions',
//       fizzbuzz:   '🎯 FizzBuzz',
//     };
//     const existing = document.getElementById('example-picker');
//     if (existing) { existing.remove(); return; }
//     const btn  = document.getElementById('btn-example');
//     const rect = btn.getBoundingClientRect();
//     const menu = document.createElement('div');
//     menu.id = 'example-picker';
//     menu.style.cssText = `position:fixed;top:${rect.bottom+6}px;right:${window.innerWidth-rect.right}px;background:var(--surface2);border:1px solid var(--border2);border-radius:var(--radius-lg);padding:6px;z-index:9000;min-width:200px;box-shadow:var(--shadow);`;
//     Object.keys(examples).forEach(key => {
//       const item = document.createElement('button');
//       item.style.cssText = `display:block;width:100%;text-align:left;padding:8px 12px;border-radius:var(--radius);font-family:var(--font-mono);font-size:12px;color:var(--text);transition:background 0.15s;cursor:pointer;background:none;border:none;`;
//       item.textContent = labels[key] || key;
//       item.addEventListener('mouseenter', () => item.style.background = 'var(--surface3)');
//       item.addEventListener('mouseleave', () => item.style.background = 'none');
//       item.addEventListener('click', () => {
//         window.EmojiEditor.setValue(examples[key]);
//         window.EmojiUI.showWelcome();
//         menu.remove();
//         window.EmojiUI.showToast(`Loaded: ${labels[key]}`, 'success');
//       });
//       menu.appendChild(item);
//     });
//     document.body.appendChild(menu);
//     document.addEventListener('click', function close(e) {
//       if (!menu.contains(e.target) && e.target !== btn) {
//         menu.remove();
//         document.removeEventListener('click', close);
//       }
//     }, { capture: true });
//   }

// })();

/**
 * app.js
 * Main entry point. Wires together all modules.
 */

(function () {

  document.addEventListener('DOMContentLoaded', () => {
    window.EmojiEditor.init();
    window.EmojiSidebar.init();
    window.EmojiUI.init();
    window.EmojiParticipant.init();

    bindButtons();
    bindTabs();
  });

  function bindButtons() {
    document.getElementById('btn-run').addEventListener('click', runCode);
    document.getElementById('btn-clear').addEventListener('click', clearEditor);
    document.getElementById('btn-example').addEventListener('click', showExamplePicker);
  }

  function bindTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        window.EmojiUI.toggleDocs(target === 'docs');
      });
    });
  }

  async function runCode() {
    const source = window.EmojiEditor.getValue().trim();
    if (!source) { window.EmojiUI.showToast('Write some emoji code first! 🖊️', 'error'); return; }

    const { python, errors } = window.EmojiCompiler.compile(source);
    if (errors.length > 0) {
      window.EmojiUI.showCompileErrors(errors);
      window.EmojiUI.showToast(`${errors.length} compile error${errors.length > 1 ? 's' : ''} found`, 'error');
      return;
    }

    const runBtn = document.getElementById('btn-run');
    runBtn.disabled = true;
    window.EmojiUI.showRunning();

    try {
      const result = await window.EmojiRunner.run(python);
      if (result.exitCode === 0 && !result.error) {
        window.EmojiUI.showSuccess(result);
        window.EmojiUI.showToast('Ran successfully ✓', 'success');
      } else {
        window.EmojiUI.showRuntimeError(result);
        window.EmojiUI.showToast('Runtime error 💥', 'error');
      }
    } catch (err) {
      window.EmojiUI.showFatalError(err.message || 'Unknown error');
      window.EmojiUI.showToast('API error', 'error');
    } finally {
      runBtn.disabled = false;
    }
  }

  function clearEditor() {
    if (!window.EmojiEditor.getValue().trim()) return;
    if (confirm('Clear the editor?')) {
      window.EmojiEditor.clear();
      window.EmojiUI.showWelcome();
      window.EmojiUI.showToast('Editor cleared', 'info');
    }
  }

  function showExamplePicker() {
    const examples = window.EMOJI_LANG.examples;
    const labels = {
      helloWorld: '👋 Hello World',
      variables:  '📦 Variables',
      ifElse:     '🤔 If / Else',
      loop:       '🔁 Loops',
      function:   '🔧 Functions',
      fizzbuzz:   '🎯 FizzBuzz',
    };
    const existing = document.getElementById('example-picker');
    if (existing) { existing.remove(); return; }
    const btn  = document.getElementById('btn-example');
    const rect = btn.getBoundingClientRect();
    const menu = document.createElement('div');
    menu.id = 'example-picker';
    menu.style.cssText = `position:fixed;top:${rect.bottom+6}px;right:${window.innerWidth-rect.right}px;background:var(--surface2);border:1px solid var(--border2);border-radius:var(--radius-lg);padding:6px;z-index:9000;min-width:200px;box-shadow:var(--shadow);`;
    Object.keys(examples).forEach(key => {
      const item = document.createElement('button');
      item.style.cssText = `display:block;width:100%;text-align:left;padding:8px 12px;border-radius:var(--radius);font-family:var(--font-mono);font-size:12px;color:var(--text);transition:background 0.15s;cursor:pointer;background:none;border:none;`;
      item.textContent = labels[key] || key;
      item.addEventListener('mouseenter', () => item.style.background = 'var(--surface3)');
      item.addEventListener('mouseleave', () => item.style.background = 'none');
      item.addEventListener('click', () => {
        window.EmojiEditor.setValue(examples[key]);
        window.EmojiUI.showWelcome();
        menu.remove();
        window.EmojiUI.showToast(`Loaded: ${labels[key]}`, 'success');
      });
      menu.appendChild(item);
    });
    document.body.appendChild(menu);
    document.addEventListener('click', function close(e) {
      if (!menu.contains(e.target) && e.target !== btn) {
        menu.remove();
        document.removeEventListener('click', close);
      }
    }, { capture: true });
  }

})();