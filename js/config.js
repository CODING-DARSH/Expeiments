/**
 * config.js
 * ← ONLY FILE YOU NEED TO EDIT FOR ALL SETTINGS
 */

window.HC_CONFIG = {

  // ── SUPABASE ──────────────────────────────────────────────────────
  SUPABASE_URL: 'https://pfcgamdlrmvbfzpgmtbe.supabase.co',
  SUPABASE_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBmY2dhbWRscm12YmZ6cGdtdGJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1MDI2NzEsImV4cCI6MjA4OTA3ODY3MX0.9Ku4UqF7vx89CT0DcpbjPv5-ZH3cSb8j3elCqMOwFZ0',

  // ── BACKEND ───────────────────────────────────────────────────────
  IS_LOCAL:        true,
  BASE_URL_LOCAL:  'http://localhost:5000',
  BASE_URL_DEPLOY: 'https://hackandcrack.onrender.com',

  // ── SECRETS ───────────────────────────────────────────────────────
  JUDGE_SECRET:   'turingtech12',

  // ── HELPER ────────────────────────────────────────────────────────
  get BASE_URL() {
    return this.IS_LOCAL ? this.BASE_URL_LOCAL : this.BASE_URL_DEPLOY;
  },

  // ── SUPABASE FETCH ────────────────────────────────────────────────
  async sbFetch(path, method = 'GET', body = null) {
    const res = await fetch(`${this.SUPABASE_URL}/rest/v1/${path}`, {
      method,
      headers: {
        'apikey':        this.SUPABASE_KEY,
        'Authorization': `Bearer ${this.SUPABASE_KEY}`,
        'Content-Type':  'application/json',
        'Prefer':        'return=representation',
      },
      body: body ? JSON.stringify(body) : null,
    });
    if (res.status === 204) return null;
    return res.json();
  }
};