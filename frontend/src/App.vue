<script setup>
import { onMounted, ref } from "vue";

const health = ref(null);
const unbound = ref([]);
const dims = ref([]);
const bound = ref([]);
const quarantine = ref([]);
const batches = ref([]);
const reconcile = ref(null);
const message = ref("");
const busy = ref(false);

const factForm = ref({
  batch_key: "fact-demo-01",
  fact_id: "F-1001",
  bind_key: "SKU-88",
  amount: 12.5,
  event_at: new Date().toISOString().slice(0, 19),
});

const dimForm = ref({
  batch_key: "dim-demo-01",
  bind_key: "SKU-88",
  version: 1,
  label: "晚到维演示",
});

const quarantineAt = ref(new Date(Date.now() - 86400000 * 30).toISOString().slice(0, 19));

async function api(path, options) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const detail = data?.detail || text || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

async function refresh() {
  const [h, u, d, b, q, bat, r] = await Promise.all([
    api("/api/health"),
    api("/api/facts/unbound"),
    api("/api/dimensions/"),
    api("/api/binder/bound"),
    api("/api/binder/quarantine"),
    api("/api/batches"),
    api("/api/reconcile"),
  ]);
  health.value = h;
  unbound.value = u;
  dims.value = d;
  bound.value = b;
  quarantine.value = q;
  batches.value = bat;
  reconcile.value = r;
}

async function withBusy(fn) {
  busy.value = true;
  message.value = "";
  try {
    await fn();
    await refresh();
  } catch (e) {
    message.value = e.message || String(e);
  } finally {
    busy.value = false;
  }
}

function ingestFacts() {
  return withBusy(async () => {
    const f = factForm.value;
    await api("/api/facts/ingest", {
      method: "POST",
      body: JSON.stringify({
        batch_key: f.batch_key,
        note: "前端演示装载",
        facts: [
          {
            fact_id: f.fact_id,
            bind_key: f.bind_key,
            amount: Number(f.amount),
            event_at: new Date(f.event_at).toISOString(),
            payload: "{}",
          },
        ],
      }),
    });
    message.value = "事实已入未绑区";
  });
}

function ingestDims() {
  return withBusy(async () => {
    const f = dimForm.value;
    await api("/api/dimensions/ingest", {
      method: "POST",
      body: JSON.stringify({
        batch_key: f.batch_key,
        note: "维度晚到装载",
        rows: [
          {
            bind_key: f.bind_key,
            version: Number(f.version),
            label: f.label,
            status: "active",
          },
        ],
      }),
    });
    message.value = "维度已装载";
  });
}

function runBind() {
  return withBusy(async () => {
    const r = await api("/api/binder/run", {
      method: "POST",
      body: JSON.stringify({ note: "手动绑定" }),
    });
    message.value = `绑定完成：成功 ${r.bound_count}，跳过 ${r.skipped_count}`;
  });
}

function runQuarantine() {
  return withBusy(async () => {
    const r = await api("/api/binder/quarantine", {
      method: "POST",
      body: JSON.stringify({
        older_than: new Date(quarantineAt.value).toISOString(),
        reason: "over_age",
      }),
    });
    message.value = `隔离移动 ${r.moved} 条`;
  });
}

onMounted(() => {
  refresh().catch((e) => {
    message.value = e.message || String(e);
  });
});
</script>

<template>
  <div class="page">
    <header class="hero">
      <p class="eyebrow">数据工程 · 晚到维度接合</p>
      <h1>晚维台 <span>Latebind</span></h1>
      <p class="lede">
        事实先入未绑区，维度晚到后再绑定入正式账；超龄未绑可隔离，并与正式区互证。
      </p>
      <div class="cta">
        <button :disabled="busy" @click="refresh">刷新状态</button>
        <button class="ghost" :disabled="busy" @click="runBind">执行绑定</button>
        <span class="health" v-if="health">服务 {{ health.ok ? "正常" : "异常" }}</span>
      </div>
      <p class="msg" v-if="message">{{ message }}</p>
    </header>

    <section class="grid">
      <article class="panel">
        <h2>装载事实 → 未绑区</h2>
        <div class="form">
          <label>批次键<input v-model="factForm.batch_key" /></label>
          <label>事实 ID<input v-model="factForm.fact_id" /></label>
          <label>绑定键<input v-model="factForm.bind_key" /></label>
          <label>金额<input v-model="factForm.amount" type="number" step="0.01" /></label>
          <label>事件时间<input v-model="factForm.event_at" /></label>
        </div>
        <button :disabled="busy" @click="ingestFacts">装载事实</button>
      </article>

      <article class="panel">
        <h2>装载维度（可晚到）</h2>
        <div class="form">
          <label>批次键<input v-model="dimForm.batch_key" /></label>
          <label>绑定键<input v-model="dimForm.bind_key" /></label>
          <label>版本<input v-model="dimForm.version" type="number" /></label>
          <label>标签<input v-model="dimForm.label" /></label>
        </div>
        <button :disabled="busy" @click="ingestDims">装载维度</button>
      </article>

      <article class="panel">
        <h2>超龄隔离</h2>
        <div class="form">
          <label>早于此时仍未绑<input v-model="quarantineAt" /></label>
        </div>
        <button :disabled="busy" @click="runQuarantine">执行隔离</button>
      </article>

      <article class="panel wide" v-if="reconcile">
        <h2>互证</h2>
        <div class="stats">
          <div><strong>{{ reconcile.unbound_count }}</strong><span>未绑</span></div>
          <div><strong>{{ reconcile.bound_count }}</strong><span>正式</span></div>
          <div><strong>{{ reconcile.quarantine_count }}</strong><span>隔离</span></div>
          <div><strong>{{ reconcile.dim_active_keys }}</strong><span>活跃维键</span></div>
        </div>
        <ul class="notes">
          <li v-for="(m, i) in reconcile.messages" :key="i">{{ m }}</li>
        </ul>
      </article>
    </section>

    <section class="tables">
      <article class="panel">
        <h2>未绑事实</h2>
        <table>
          <thead>
            <tr>
              <th>fact_id</th>
              <th>bind_key</th>
              <th>amount</th>
              <th>batch</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in unbound" :key="r.fact_id">
              <td>{{ r.fact_id }}</td>
              <td>{{ r.bind_key }}</td>
              <td>{{ r.amount }}</td>
              <td>{{ r.batch_key }}</td>
            </tr>
          </tbody>
        </table>
      </article>

      <article class="panel">
        <h2>维度</h2>
        <table>
          <thead>
            <tr>
              <th>bind_key</th>
              <th>ver</th>
              <th>label</th>
              <th>status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in dims" :key="r.bind_key + r.version">
              <td>{{ r.bind_key }}</td>
              <td>{{ r.version }}</td>
              <td>{{ r.label }}</td>
              <td>{{ r.status }}</td>
            </tr>
          </tbody>
        </table>
      </article>

      <article class="panel">
        <h2>正式绑定</h2>
        <table>
          <thead>
            <tr>
              <th>fact_id</th>
              <th>bind_key</th>
              <th>dim</th>
              <th>amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in bound" :key="r.fact_id">
              <td>{{ r.fact_id }}</td>
              <td>{{ r.bind_key }}</td>
              <td>{{ r.dim_label }}@v{{ r.dim_version }}</td>
              <td>{{ r.amount }}</td>
            </tr>
          </tbody>
        </table>
      </article>

      <article class="panel">
        <h2>隔离区</h2>
        <table>
          <thead>
            <tr>
              <th>fact_id</th>
              <th>bind_key</th>
              <th>reason</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in quarantine" :key="r.fact_id">
              <td>{{ r.fact_id }}</td>
              <td>{{ r.bind_key }}</td>
              <td>{{ r.reason }}</td>
            </tr>
          </tbody>
        </table>
      </article>

      <article class="panel wide">
        <h2>装载批次</h2>
        <table>
          <thead>
            <tr>
              <th>batch_key</th>
              <th>kind</th>
              <th>rows</th>
              <th>note</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in batches" :key="r.batch_key">
              <td>{{ r.batch_key }}</td>
              <td>{{ r.kind }}</td>
              <td>{{ r.row_count }}</td>
              <td>{{ r.note }}</td>
            </tr>
          </tbody>
        </table>
      </article>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 2rem 1.25rem 4rem;
}

.hero {
  margin-bottom: 2rem;
}

.eyebrow {
  color: var(--accent);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.78rem;
  margin: 0 0 0.6rem;
}

h1 {
  font-family: var(--font-display);
  font-size: clamp(2.4rem, 5vw, 3.6rem);
  line-height: 1.05;
  margin: 0 0 0.75rem;
  font-weight: 800;
}

h1 span {
  color: var(--accent);
  font-weight: 700;
}

.lede {
  max-width: 42rem;
  color: var(--muted);
  margin: 0 0 1.25rem;
  line-height: 1.6;
}

.cta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.health {
  color: var(--ok);
  font-size: 0.9rem;
}

.msg {
  margin-top: 0.85rem;
  color: var(--warn);
}

.grid,
.tables {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.panel {
  background: color-mix(in srgb, var(--panel) 88%, black);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 1rem 1.1rem 1.15rem;
  min-width: 0;
}

.panel.wide {
  grid-column: 1 / -1;
}

h2 {
  font-family: var(--font-display);
  font-size: 1.15rem;
  margin: 0 0 0.85rem;
}

.form {
  display: grid;
  gap: 0.55rem;
  margin-bottom: 0.85rem;
}

label {
  display: grid;
  gap: 0.25rem;
  color: var(--muted);
  font-size: 0.85rem;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.stats strong {
  display: block;
  font-family: var(--font-display);
  font-size: 1.6rem;
  color: var(--accent);
}

.stats span {
  color: var(--muted);
  font-size: 0.85rem;
}

.notes {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--muted);
}

@media (max-width: 960px) {
  .grid,
  .tables {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
