"""
pyPreservica storage usage report module definition

Walks a Preservica folder hierarchy (or the whole repository), sums the size of the
bitstreams held by each asset and folder, and renders the result as an interactive,
self-contained HTML page with a radial "sunburst" chart in the style of the
KDE Filelight disk usage application.

author:     James Carr
licence:    Apache License 2.0

"""

import html
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Union, Optional, Iterable, Callable

from tqdm import tqdm

from pyPreservica.common import Folder, Asset, Entity, EntityType, RepresentationType, AuthenticatedAPI
from pyPreservica.entityAPI import EntityAPI

logger = logging.getLogger(__name__)



class StorageNode:
    """
    A node in the storage usage tree, either a folder or an asset.

    :param reference: The Preservica entity reference, ``None`` for the repository root.
    :param title: The entity title.
    :param entity_type: ``EntityType.FOLDER`` or ``EntityType.ASSET``.
    """

    def __init__(self, reference: Optional[str], title: str, entity_type: EntityType):
        self.reference = reference
        self.title = title
        self.entity_type = entity_type
        self.size: int = 0
        self.asset_count: int = 0
        self.bitstream_count: int = 0
        self.children: list["StorageNode"] = []

    @property
    def is_folder(self) -> bool:
        return self.entity_type == EntityType.FOLDER

    def to_dict(self) -> dict:
        """ Return the node, and all its children, as a dictionary suitable for JSON serialisation """
        node = {"ref": self.reference, "name": self.title, "type": "F" if self.is_folder else "A",
                "size": self.size, "assets": self.asset_count, "files": self.bitstream_count}
        if self.children:
            node["children"] = [c.to_dict() for c in self.children]
        return node

    @staticmethod
    def from_dict(data: dict) -> "StorageNode":
        """ Rebuild a storage tree from a dictionary created by to_dict() """
        node = StorageNode(data.get("ref"), data.get("name"),
                           EntityType.FOLDER if data.get("type") == "F" else EntityType.ASSET)
        node.size = int(data.get("size", 0))
        node.asset_count = int(data.get("assets", 0))
        node.bitstream_count = int(data.get("files", 0))
        node.children = [StorageNode.from_dict(c) for c in data.get("children", [])]
        return node

    def __str__(self):
        return f"{self.title} ({self.reference}): {human_size(self.size)}"

    def __repr__(self):
        return self.__str__()


def human_size(num_bytes: int) -> str:
    """
    Format a byte count as a human readable string using binary units, e.g. ``1.5 GiB``

    :param num_bytes: The number of bytes
    :return: The formatted string
    """
    size = float(num_bytes)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
        if abs(size) < 1024.0 or unit == "PiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PiB"


class StorageUsageReport:
    """
    Calculate and visualise the storage used by a Preservica folder hierarchy.

    The report walks the folder tree using the Entity API, sums the size of the active
    generation bitstreams of every asset, and can render the result as an interactive
    HTML sunburst chart in the style of KDE Filelight.

    Sizing an asset needs several API calls (representations, content objects, generations
    and bitstreams), so assets are sized in parallel using a pool of worker threads.

    :param client: An authenticated EntityAPI client.
    :param representation_types: The representation types to include in the totals.
        Defaults to both Preservation and Access representations.
    :param max_workers: The number of worker threads used to size assets in parallel.
    :param show_progress: Display a progress bar on the console while scanning.
    """

    def __init__(self, client: EntityAPI,
                 representation_types: Iterable[RepresentationType] = (RepresentationType.Preservation,
                                                                        RepresentationType.Access),
                 max_workers: int = 4, show_progress: bool = True):
        self.client = client
        self.representation_types = set(representation_types)
        self.max_workers = max(1, int(max_workers))
        self.show_progress = show_progress
        self.root: Optional[StorageNode] = None
        self.scanned_at: Optional[datetime] = None
        self.server: Optional[str] = getattr(client, "server", None)
        self.tenant: Optional[str] = getattr(client, "tenant", None)

    def _asset_size(self, asset: Asset) -> tuple[int, int]:
        """
        Return the total size in bytes and number of bitstreams of the active generations of an asset
        """
        total = 0
        count = 0
        seen = set()
        for representation in self.client.representations(asset):
            if representation.rep_type not in self.representation_types:
                continue
            for content_object in self.client.content_objects(representation):
                for generation in self.client.generations(content_object):
                    if not generation.active:
                        continue
                    for bitstream in generation.bitstreams:
                        key = bitstream.content_url or (content_object.reference, bitstream.filename)
                        if key in seen:
                            continue
                        seen.add(key)
                        total += int(bitstream.length or 0)
                        count += 1
        return total, count

    def _size_asset_node(self, node: StorageNode) -> StorageNode:
        try:
            node.size, node.bitstream_count = self._asset_size(Asset(node.reference, node.title))
        except Exception as e:
            logger.warning(f"Unable to calculate the size of asset {node.reference}: {e}")
        node.asset_count = 1
        return node

    def _build_tree(self, node: StorageNode, parent: Union[Folder, None], assets: list[StorageNode],
                    progress: Optional[Callable]):
        """ Walk the folder hierarchy, collecting asset nodes to be sized later """
        for entity in self.client.descendants(parent):
            child = StorageNode(entity.reference, entity.title, entity.entity_type)
            node.children.append(child)
            if entity.entity_type == EntityType.FOLDER:
                self._build_tree(child, entity, assets, progress)
            else:
                assets.append(child)
                if progress:
                    progress()

    @staticmethod
    def _roll_up(node: StorageNode):
        """ Sum the sizes of child nodes into their parent folders and sort children largest first """
        if not node.is_folder:
            return
        node.size = 0
        node.asset_count = 0
        node.bitstream_count = 0
        for child in node.children:
            StorageUsageReport._roll_up(child)
            node.size += child.size
            node.asset_count += child.asset_count
            node.bitstream_count += child.bitstream_count
        node.children.sort(key=lambda c: c.size, reverse=True)

    def scan(self, folder: Union[Folder, Entity, str, None] = None) -> StorageNode:
        """
        Scan a folder hierarchy and calculate the storage used by every folder and asset.

        :param folder: The folder (or folder reference) to start from, ``None`` for the whole repository.
        :return: The root StorageNode of the scanned tree.
        """
        if isinstance(folder, str):
            folder = self.client.folder(folder)
        if folder is None:
            root = StorageNode(None, "Repository", EntityType.FOLDER)
        else:
            root = StorageNode(folder.reference, folder.title, EntityType.FOLDER)

        assets: list[StorageNode] = []
        with tqdm(desc="Scanning folders", unit=" assets", disable=not self.show_progress) as bar:
            self._build_tree(root, folder, assets, lambda: bar.update(1))

        with tqdm(total=len(assets), desc="Sizing assets", unit=" assets", disable=not self.show_progress) as bar:
            if self.max_workers == 1:
                for node in assets:
                    self._size_asset_node(node)
                    bar.update(1)
            else:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    for _ in executor.map(self._size_asset_node, assets):
                        bar.update(1)

        self._roll_up(root)
        self.root = root
        self.scanned_at = datetime.now()
        return root

    def _require_scan(self):
        if self.root is None:
            raise RuntimeError("No scan results, call scan() or load_json() first")

    def to_dict(self) -> dict:
        """ Return the scan results as a dictionary """
        self._require_scan()
        return {"server": self.server, "tenant": self.tenant,
                "scanned": self.scanned_at.isoformat(timespec="seconds") if self.scanned_at else None,
                "tree": self.root.to_dict()}

    def save_json(self, filename: str) -> str:
        """
        Save the scan results to a JSON file, so the report can be re-rendered without re-scanning.

        :param filename: The JSON file to write
        :return: The filename
        """
        with open(filename, "w", encoding="utf-8") as fd:
            json.dump(self.to_dict(), fd)
        return filename

    def load_json(self, filename: str) -> StorageNode:
        """
        Load scan results previously saved with save_json()

        :param filename: The JSON file to read
        :return: The root StorageNode
        """
        with open(filename, "r", encoding="utf-8") as fd:
            data = json.load(fd)
        self.root = StorageNode.from_dict(data["tree"])
        scanned = data.get("scanned")
        self.scanned_at = datetime.fromisoformat(scanned) if scanned else None
        self.server = data.get("server") or self.server
        self.tenant = data.get("tenant") or self.tenant
        return self.root

    def largest(self, limit: int = 10, entity_type: EntityType = EntityType.ASSET) -> list[StorageNode]:
        """
        Return the largest folders or assets in the scanned tree

        :param limit: The number of entities to return
        :param entity_type: Either EntityType.ASSET or EntityType.FOLDER
        :return: A list of StorageNode objects, largest first
        """
        self._require_scan()
        found = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.entity_type == entity_type and node is not self.root:
                found.append(node)
            stack.extend(node.children)
        found.sort(key=lambda n: n.size, reverse=True)
        return found[:limit]

    def render_html(self, filename: str = "storage_usage.html", title: Optional[str] = None) -> str:
        """
        Render the scan results as a self-contained interactive HTML page containing a
        Filelight style sunburst chart and a sortable list of the folder contents.

        The page has no external dependencies and can be opened directly in a web browser.

        :param filename: The HTML file to write
        :param title: The page title, defaults to the name of the scanned folder
        :return: The filename
        """
        self._require_scan()
        data = self.to_dict()
        page_title = title or f"Storage usage: {self.root.title}"
        payload = json.dumps(data).replace("</", "<\\/")
        document = _HTML_TEMPLATE.replace("__TITLE__", html.escape(page_title)).replace("__DATA__", payload)
        with open(filename, "w", encoding="utf-8") as fd:
            fd.write(document)
        return filename


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --bg:#eff0f1; --panel:#fff; --text:#232629; --muted:#7f8c8d; --border:#d1d3d5;
        --hover:#e3eef9; --sel:#3daee9; --bar:#dfe1e3; --stroke:#232629; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --bg:#202326; --panel:#2a2e32; --text:#fcfcfc; --muted:#a1a9b1;
        --border:#3c4146; --hover:#33404d; --sel:#3daee9; --bar:#31363b; --stroke:#141618; }
}
* { box-sizing:border-box; }
html,body { margin:0; height:100%; }
body { background:var(--bg); color:var(--text); font:14px/1.35 "Noto Sans", "Segoe UI", system-ui, sans-serif;
       display:flex; flex-direction:column; }
header { display:flex; align-items:center; gap:4px; padding:6px 10px; background:var(--bar);
         border-bottom:1px solid var(--border); flex-wrap:wrap; }
header h1 { font-size:15px; font-weight:600; margin:0 auto 0 4px; white-space:nowrap; overflow:hidden;
            text-overflow:ellipsis; }
#source { display:flex; gap:6px 24px; padding:8px 14px; background:var(--panel); border-bottom:1px solid var(--border);
          flex-wrap:wrap; font-size:13px; }
#source:empty { display:none; }
#source div { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
#source span { color:var(--muted); margin-right:6px; }
#source b { font-weight:600; }
button { background:none; border:1px solid transparent; border-radius:4px; color:var(--text); font:inherit;
         padding:4px 10px; cursor:pointer; }
button:hover:not(:disabled) { background:var(--hover); border-color:var(--border); }
button:disabled { color:var(--muted); cursor:default; }
#crumbs { padding:6px 12px; font-size:13px; color:var(--muted); border-bottom:1px solid var(--border);
          background:var(--panel); white-space:nowrap; overflow-x:auto; }
#crumbs a { color:var(--text); cursor:pointer; text-decoration:none; }
#crumbs a:hover { text-decoration:underline; }
main { flex:1; display:flex; min-height:0; }
#list { width:340px; min-width:220px; background:var(--panel); border-right:1px solid var(--border);
        overflow-y:auto; }
.row { display:flex; gap:10px; padding:7px 12px; cursor:pointer; align-items:center; }
.row:hover, .row.hl { background:var(--hover); }
.sw { width:12px; height:12px; border-radius:2px; flex:none; border:1px solid var(--stroke); }
.row .n { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.row .s { font-size:12px; color:var(--muted); }
.row .txt { min-width:0; flex:1; }
.row .pct { font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; }
#chart { flex:1; display:flex; align-items:center; justify-content:center; min-width:0; position:relative; }
#chart svg { width:100%; height:100%; max-height:100%; }
#chart path { stroke:var(--stroke); stroke-width:0.6; cursor:pointer; }
#chart path:hover, #chart path.hl { filter:brightness(1.15) saturate(1.2); }
#centre { cursor:pointer; }
#tip { position:fixed; pointer-events:none; background:var(--panel); color:var(--text); border:1px solid var(--border);
       border-radius:4px; padding:6px 9px; font-size:13px; box-shadow:0 2px 8px rgba(0,0,0,.2); display:none;
       max-width:360px; z-index:5; }
#tip b { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
#tip span { color:var(--muted); font-size:12px; }
footer { display:flex; justify-content:space-between; gap:12px; padding:5px 12px; background:var(--bar);
         border-top:1px solid var(--border); font-size:13px; flex-wrap:wrap; }
@media (max-width: 720px) {
  main { flex-direction:column-reverse; }
  #list { width:auto; border-right:none; border-top:1px solid var(--border); max-height:45vh; }
  #chart { min-height:55vh; }
}
</style>
</head>
<body>
<div id="source"></div>
<header>
  <h1 id="title"></h1>
  <button id="back" title="Back">&#8592; Back</button>
  <button id="fwd" title="Forward">Forward &#8594;</button>
  <button id="up" title="Up one level">&#8593; Up</button>
  <button id="home" title="Go to overview">&#8962; Overview</button>
</header>
<div id="crumbs"></div>
<main>
  <div id="list"></div>
  <div id="chart"><svg id="svg" viewBox="-340 -340 680 680" role="img" aria-label="Storage usage chart"></svg></div>
</main>
<footer><span id="status"></span><span id="counts"></span></footer>
<div id="tip"></div>
<script>
const DATA = __DATA__;
const RINGS = 5, INNER = 60, RING = 46, MIN_ANGLE = 0.012;
const svg = document.getElementById('svg'), list = document.getElementById('list'), tip = document.getElementById('tip');
const NS = 'http://www.w3.org/2000/svg';
let current = null, history = [], future = [];

(function link(n, p) { n.parent = p; (n.children || []).forEach(c => link(c, n)); })(DATA.tree, null);

function fmt(b) {
  const u = ['B','KiB','MiB','GiB','TiB','PiB']; let i = 0; b = Number(b);
  while (Math.abs(b) >= 1024 && i < u.length - 1) { b /= 1024; i++; }
  return i === 0 ? b + ' B' : b.toFixed(1) + ' ' + u[i];
}
function num(n) { return Number(n).toLocaleString(); }
function isFolder(n) { return n.type === 'F'; }

function colour(node, depth, midAngle) {
  if (node.grouped) return 'hsl(0,0%,82%)';
  if (!isFolder(node)) return `hsl(${Math.round(midAngle * 180 / Math.PI)},12%,${Math.min(88, 70 + depth * 3)}%)`;
  const hue = Math.round(midAngle * 180 / Math.PI);
  return `hsl(${hue},${Math.max(45, 80 - depth * 7)}%,${Math.min(78, 52 + depth * 6)}%)`;
}

function arc(r0, r1, a0, a1) {
  if (a1 - a0 >= 2 * Math.PI - 1e-6) a1 = a0 + 2 * Math.PI - 1e-4;
  const large = (a1 - a0) > Math.PI ? 1 : 0;
  const p = (r, a) => `${(r * Math.cos(a - Math.PI / 2)).toFixed(2)},${(r * Math.sin(a - Math.PI / 2)).toFixed(2)}`;
  return `M${p(r1, a0)}A${r1},${r1} 0 ${large} 1 ${p(r1, a1)}L${p(r0, a1)}A${r0},${r0} 0 ${large} 0 ${p(r0, a0)}Z`;
}

function segments(node, a0, a1, depth, out) {
  if (depth > RINGS || !node.children || node.size <= 0) return;
  let a = a0, small = [];
  for (const c of node.children) {
    const span = (a1 - a0) * (c.size / node.size);
    if (span < MIN_ANGLE) { small.push(c); continue; }
    out.push({node: c, a0: a, a1: a + span, depth});
    if (isFolder(c)) segments(c, a, a + span, depth + 1, out);
    a += span;
  }
  if (small.length) {
    const size = small.reduce((s, c) => s + c.size, 0), span = (a1 - a0) * (size / node.size);
    if (span > 0.002) out.push({node: {name: `${small.length} small items`, size, grouped: true, parent: node,
                                       assets: small.reduce((s, c) => s + c.assets, 0),
                                       files: small.reduce((s, c) => s + c.files, 0), type: 'G'},
                                a0: a, a1: a + span, depth});
  }
}

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

function showTip(ev, n) {
  const share = current.size ? (100 * n.size / current.size).toFixed(1) + '%' : '';
  tip.innerHTML = '';
  const b = document.createElement('b'); b.textContent = n.name || '(untitled)'; tip.appendChild(b);
  const s = document.createElement('span');
  s.textContent = `${fmt(n.size)} · ${share} · ${num(n.assets)} asset${n.assets === 1 ? '' : 's'}, ${num(n.files)} file${n.files === 1 ? '' : 's'}`;
  tip.appendChild(s);
  if (n.ref) { const r = document.createElement('span'); r.style.display = 'block'; r.textContent = n.ref; tip.appendChild(r); }
  tip.style.display = 'block';
  const x = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
  const y = Math.min(ev.clientY + 14, window.innerHeight - tip.offsetHeight - 8);
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
function hideTip() { tip.style.display = 'none'; }

function highlight(n, on) {
  document.querySelectorAll('[data-id]').forEach(e => { if (e._node === n) e.classList.toggle('hl', on); });
}

function activate(n) {
  if (!n || n.grouped) return;
  if (isFolder(n) && n.children && n.children.length) go(n);
}

function drawChart() {
  svg.innerHTML = '';
  const segs = []; segments(current, 0, 2 * Math.PI, 0, segs);
  let id = 0;
  for (const s of segs) {
    const mid = (s.a0 + s.a1) / 2;
    const p = el('path', {d: arc(INNER + s.depth * RING, INNER + (s.depth + 1) * RING - 1, s.a0, s.a1),
                          fill: colour(s.node, s.depth, mid), 'data-id': id++}, svg);
    p._node = s.node;
    p.addEventListener('mousemove', ev => showTip(ev, s.node));
    p.addEventListener('mouseenter', () => highlight(s.node, true));
    p.addEventListener('mouseleave', () => { hideTip(); highlight(s.node, false); });
    p.addEventListener('click', () => { hideTip(); activate(s.node); });
  }
  const c = el('circle', {r: INNER - 2, fill: 'var(--panel)', stroke: 'var(--border)', id: 'centre'}, svg);
  c.addEventListener('click', () => { if (current.parent) go(current.parent); });
  el('title', {}, c).textContent = current.parent ? 'Up one level' : current.name;
  const t = el('text', {'text-anchor': 'middle', 'dominant-baseline': 'middle', fill: 'var(--text)',
                        'font-size': 15, 'font-weight': 600, 'pointer-events': 'none'}, svg);
  t.textContent = fmt(current.size);
  if (!segs.length) {
    const e = el('text', {'text-anchor': 'middle', y: INNER + 30, fill: 'var(--muted)', 'font-size': 14}, svg);
    e.textContent = current.size ? 'Contents too small to display' : 'This folder is empty';
  }
}

function drawList() {
  list.innerHTML = '';
  const kids = current.children || [];
  if (!kids.length) {
    const d = document.createElement('div'); d.className = 'row'; d.style.cursor = 'default';
    d.textContent = 'No child folders or assets'; list.appendChild(d); return;
  }
  const n = kids.length;
  kids.forEach((k, i) => {
    const row = document.createElement('div'); row.className = 'row'; row.dataset.id = 'l' + i; row._node = k;
    const sw = document.createElement('span'); sw.className = 'sw';
    let a = 0; for (let j = 0; j < i; j++) a += kids[j].size;
    const mid = current.size ? 2 * Math.PI * (a + k.size / 2) / current.size : 0;
    sw.style.background = colour(k, 0, mid); row.appendChild(sw);
    const txt = document.createElement('div'); txt.className = 'txt';
    const nm = document.createElement('div'); nm.className = 'n';
    nm.textContent = (k.name || '(untitled)') + (isFolder(k) ? '/' : '');
    const sz = document.createElement('div'); sz.className = 's';
    sz.textContent = `${fmt(k.size)} · ${num(k.assets)} asset${k.assets === 1 ? '' : 's'}`;
    txt.appendChild(nm); txt.appendChild(sz); row.appendChild(txt);
    const pct = document.createElement('span'); pct.className = 'pct';
    pct.textContent = current.size ? (100 * k.size / current.size).toFixed(1) + '%' : '';
    row.appendChild(pct);
    row.title = k.ref || '';
    if (!isFolder(k)) row.style.cursor = 'default';
    row.addEventListener('mouseenter', () => highlight(k, true));
    row.addEventListener('mouseleave', () => highlight(k, false));
    row.addEventListener('click', () => activate(k));
    list.appendChild(row);
  });
}

function drawCrumbs() {
  const c = document.getElementById('crumbs'); c.innerHTML = '';
  const path = []; for (let n = current; n; n = n.parent) path.unshift(n);
  path.forEach((n, i) => {
    if (i) c.appendChild(document.createTextNode(' / '));
    const a = document.createElement('a'); a.textContent = n.name || '(untitled)';
    a.addEventListener('click', () => { if (n !== current) go(n); }); c.appendChild(a);
  });
}

function render() {
  document.getElementById('title').textContent = current.name || 'Repository';
  document.getElementById('back').disabled = !history.length;
  document.getElementById('fwd').disabled = !future.length;
  document.getElementById('up').disabled = !current.parent;
  document.getElementById('home').disabled = current === DATA.tree;
  document.getElementById('status').textContent =
    DATA.scanned ? 'Scanned ' + DATA.scanned.replace('T', ' ') : '';
  document.getElementById('counts').textContent =
    `${fmt(current.size)} · ${num(current.assets)} assets · ${num(current.files)} files`;
  drawCrumbs(); drawList(); drawChart();
}

function go(n, keepFuture) { if (n === current) return; history.push(current); if (!keepFuture) future = []; current = n; render(); }
document.getElementById('back').onclick = () => { if (history.length) { future.push(current); current = history.pop(); render(); } };
document.getElementById('fwd').onclick = () => { if (future.length) { history.push(current); current = future.pop(); render(); } };
document.getElementById('up').onclick = () => { if (current.parent) go(current.parent); };
document.getElementById('home').onclick = () => go(DATA.tree);
document.addEventListener('keydown', e => {
  if (e.key === 'Backspace' || (e.altKey && e.key === 'ArrowUp')) { e.preventDefault(); document.getElementById('up').click(); }
  else if (e.altKey && e.key === 'ArrowLeft') document.getElementById('back').click();
  else if (e.altKey && e.key === 'ArrowRight') document.getElementById('fwd').click();
});

(function source() {
  const box = document.getElementById('source');
  for (const [label, value] of [['Tenancy', DATA.tenant], ['Server', DATA.server]]) {
    if (!value) continue;
    const d = document.createElement('div'), l = document.createElement('span'), v = document.createElement('b');
    l.textContent = label; v.textContent = value; d.appendChild(l); d.appendChild(v); box.appendChild(d);
  }
})();

current = DATA.tree; render();
</script>
</body>
</html>
"""


class ReportingAPI(AuthenticatedAPI):
    """
    API for generating reports about the content of a Preservica repository.

    Authenticates in the same way as the other pyPreservica API classes, using explicit arguments,
    environment variables or a ``credentials.properties`` file.

    Reports which need to walk the repository use an ``EntityAPI`` client, which is created with the
    same credentials the first time it is needed and then reused for later reports.
    """

    def __init__(self, username: str|None = None, password: str|None = None, tenant: str|None = None, server: str|None = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str|None = None,
                 protocol: str = "https", request_hook: Callable|None = None, credentials_path: str = 'credentials.properties'):
        self.request_hook = request_hook
        self.credentials_path = credentials_path
        self._entity_client: Optional[EntityAPI] = None

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)

    @property
    def entity_client(self) -> EntityAPI:
        """
        The EntityAPI client used to walk the repository, created on first use with the same credentials
        """
        if self._entity_client is None:
            self._entity_client = EntityAPI(username=self.username, password=self.password, server=self.server,
                                            tenant=self.tenant, use_shared_secret=self.shared_secret,
                                            two_fa_secret_key=self.two_fa_secret_key, protocol=self.protocol,
                                            request_hook=self.request_hook, credentials_path=self.credentials_path)
        return self._entity_client

    def storage_usage_report(self, folder: Union[Folder, Entity, str, None] = None,
                             filename: str = "storage_usage.html",
                             representation_types: Iterable[RepresentationType] = (RepresentationType.Preservation,
                                                                                    RepresentationType.Access),
                             max_workers: int = 4, show_progress: bool = True) -> StorageUsageReport:
        """
        Scan a folder (or the whole repository when folder is None) and write a Filelight
        style storage usage HTML report.

        :param folder: The folder or folder reference to scan, None for the repository root
        :param filename: The HTML file to write
        :param representation_types: The representation types to include in the totals.
            Defaults to both Preservation and Access representations.
        :param max_workers: The number of worker threads used to size assets
        :param show_progress: Display progress bars on the console
        :return: The StorageUsageReport, which can be used to save the results as JSON
        """
        report = StorageUsageReport(self.entity_client, representation_types=representation_types,
                                    max_workers=max_workers, show_progress=show_progress)
        report.scan(folder)
        report.render_html(filename)
        return report
