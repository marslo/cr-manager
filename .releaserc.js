// =============================================================================
// Self-contained changelog config.
//
// WHY THE TEMPLATES ARE INLINED HERE:
//   @semantic-release/release-notes-generator renders with the Handlebars-based conventional-changelog-writer. conventional-changelog-conventionalcommits >= 9 dropped its Handlebars writerOpts in favour of @conventional-changelog/ template, which release-notes-generator does NOT use — so with preset >= 9 the section grouping silently disappears (flat list, no "### Features").
//   To stay compatible with ANY preset version (8, 9, 10, …) we supply the full Handlebars writerOpts (mainTemplate / headerPartial / commitPartial) and the grouping ourselves; the preset is then only used for its commit PARSER.
//
// WRITER 8 vs 9:
//   semantic-release >= 26 bundles release-notes-generator 15 + conventional-changelog-writer 9, which dropped Handlebars: it ignores
//   `mainTemplate` and renders via `writerOpts.template( context )`, a plain function. writer 8 never reads `template`, so both are supplied:
//   writer 8 → Handlebars strings below; writer 9 → renderChangelog(), which produces the same markdown.
// =============================================================================

const SECTIONS = [
  { type: 'feat',     section: 'Features' },
  { type: 'fix',      section: 'Bug Fixes' },
  { type: 'refactor', section: 'Code Refactoring' },
  { type: 'style',    section: 'Styles' },
  { type: 'chore',    section: 'Others' },
  { type: 'docs',     section: 'Documentation' },
  { type: 'perf',     section: 'Performance' },
  { type: 'test',     section: 'Tests' },
  { type: 'ci',       section: 'CI/CD' }
];
const TYPE_TO_SECTION = Object.fromEntries(SECTIONS.map(s => [s.type, s.section]));
const SECTION_ORDER   = SECTIONS.map(s => s.section);
const isSignoff       = (line) => /^\s*Signed-off-by:/i.test(line);
const stripSignoff    = (text) => (text || '').split('\n').filter(l => !isSignoff(l)).join('\n').trim();
// `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer; already rendered from `notes` under "### ⚠ BREAKING CHANGES"
const isNoteStart     = (line) => /^\s*BREAKING[ -]CHANGES?:/.test(line);
// git trailer line, e.g. "Closes #12", "Refs: …", "Co-authored-by: …"
const isTrailer       = (line) => /^\s*[\w-]+(?::\s|\s#)/.test(line);
// drop each note block (keyword line + continuation lines, up to a blank line or the next trailer)
const stripNotes      = (lines) => {
  let inNote = false;
  return lines.filter(l => {
    if (isNoteStart(l)) { inNote = true; return false; }
    if (inNote && (l.trim() === '' || isTrailer(l))) { inNote = false; }
    return !inNote;
  });
};

// ── Handlebars templates (writer-8 compatible; vendored from the conventional-commits preset so they work regardless of the installed preset major) ──
const mainTemplate = `{{> header}}
{{#if noteGroups}}
{{#each noteGroups}}

### ⚠ {{title}}

{{#each notes}}
* {{#if commit.scope}}**{{commit.scope}}:** {{/if}}{{text}}
{{/each}}
{{/each}}
{{/if}}
{{#each commitGroups}}

{{#if title}}
### {{title}}

{{/if}}
{{#each commits}}
{{> commit root=@root}}
{{/each}}
{{/each}}
`;

const headerPartial = `## {{#if @root.linkCompare~}}
  [{{version}}]({{~@root.host}}/{{#if this.owner}}{{~this.owner}}{{else}}{{~@root.owner}}{{/if}}/{{#if this.repository}}{{~this.repository}}{{else}}{{~@root.repository}}{{/if}}/compare/{{previousTag}}...{{currentTag}})
{{~else}}
  {{~version}}
{{~/if}}
{{~#if date}} ({{date}})
{{/if}}
`;

// commit line: bold each comma-split scope as **scope:** (built as scopeFmt in transform) and keep the subject. PR commits carry an inline
// "(#N)" that GitHub auto-links, so leave them link-free; only direct pushes (no "(#N)") get an
// appended ([shortHash](…/commit/<hash>)) link. body/footer follow (built in transform)
const commitPartial =
  '*{{#if scopeFmt}} {{scopeFmt}}:{{/if}} {{#if subject}}{{subject}}{{else}}{{header}}{{/if}}' +
  '{{#unless hasIssueRef}}{{#if @root.linkReferences}} ([{{shortHash}}]({{@root.host}}/{{@root.owner}}/{{@root.repository}}/commit/{{hash}})){{/if}}{{/unless}}' +
  '\n{{#if body}}\n{{body}}\n{{/if}}\n{{#if footer}}\n\n{{footer}}\n{{/if}}\n';

// ── writer-9 template: same output as mainTemplate + headerPartial + commitPartial above ──
const renderHeader = (ctx) => {
  const version = ctx.linkCompare
    ? `[${ctx.version}](${ctx.host}/${ctx.owner}/${ctx.repository}/compare/${ctx.previousTag}...${ctx.currentTag})`
    : ctx.version;
  return `## ${version}${ctx.date ? ` (${ctx.date})` : ''}\n`;
};
const renderCommit = (c, ctx) => {
  const text = c.subject || c.header;
  const link = !c.hasIssueRef && ctx.linkReferences
    ? ` ([${c.shortHash}](${ctx.host}/${ctx.owner}/${ctx.repository}/commit/${c.hash}))`
    : '';
  return `*${c.scopeFmt ? ` ${c.scopeFmt}:` : ''} ${text}${link}\n${c.body ? `${c.body}\n` : ''}`;
};
const renderChangelog = (ctx) => {
  const notes = (ctx.noteGroups || []).map(g =>
    `\n### ⚠ ${g.title}\n\n` + g.notes.map(n => `* ${n.commit.scope ? `**${n.commit.scope}:** ` : ''}${n.text}\n`).join('')
  );
  const groups = (ctx.commitGroups || []).map(g =>
    '\n' + (g.title ? `### ${g.title}\n\n` : '') + g.commits.map(c => renderCommit(c, ctx)).join('')
  );
  return renderHeader(ctx) + notes.join('') + groups.join('');
};

// ── dynamic changelog title ──
// reuse an existing level-1 header (`# ...`) at the very top of CHANGELOG.md so new
// releases are inserted BELOW it; if there is none, leave changelogTitle unset so
// semantic-release just prepends (no title is forced onto title-less changelogs)
const fs = require('fs');
const path = require('path');
const CHANGELOG_FILE = 'CHANGELOG.md';
function detectChangelogTitle(file) {
  try {
    const text = fs.readFileSync(path.resolve(process.cwd(), file), 'utf8');
    const first = text.split('\n').find(l => l.trim() !== '');
    // a single '#' ATX header (rejects '##', '###', …) with actual text
    if (first && /^#\s+\S/.test(first)) { return first.trim(); }
  } catch (e) { /* missing or unreadable → treat as no title */ }
  return null;
}
const CHANGELOG_TITLE = detectChangelogTitle(CHANGELOG_FILE);

module.exports = {
  "branches": [
    { "name": "main" },
    { "name": "next", "channel": "beta", "prerelease": true }
  ],
  "tagFormat": "v${version}",
  "plugins": [
    ["@semantic-release/commit-analyzer", {
      "preset": "conventionalcommits",
      "releaseRules": [
        // { "breaking": true,   "release": "minor" },
        { "breaking": true,   "release": "major" },
        // { "type": "feat",     "release": "patch" },
        { "type": "chore",    "release": "patch" },
        { "type": "refactor", "release": "patch" },
        { "type": "style",    "release": "patch" },
        { "type": "docs",     "release": "patch" },
        { "type": "ci",       "release": "patch" }
      ]
    }],
    ["@semantic-release/release-notes-generator", {
      "preset": "conventionalcommits",
      "presetConfig": { "types": SECTIONS },
      "writerOpts": {
        "groupBy": "type",
        // order sections as listed in SECTIONS (not alphabetically); unknown types go last
        "commitGroupsSort": (a, b) => {
          const rank = (t) => { const i = SECTION_ORDER.indexOf(t); return i === -1 ? SECTION_ORDER.length : i; };
          return rank(a.title) - rank(b.title);
        },
        "commitsSort": ["header", "subject"],
        "noteGroupsSort": "title",
        "mainTemplate": mainTemplate,
        "headerPartial": headerPartial,
        "commitPartial": commitPartial,
        "footerPartial": "",
        // writer 9 only ( ignored by writer 8 )
        "template": renderChangelog,
        "transform": (commit) => {
          const c = { ...commit };

          // type -> section label (drives the "### <section>" grouping)
          if (TYPE_TO_SECTION[c.type]) {
            c.type = TYPE_TO_SECTION[c.type];
          }

          // preset's default transform (overridden here) normally sets shortHash; restore it
          // so the commit link text isn't empty ("[](…/commit/<hash>)")
          if (typeof c.hash === 'string') {
            c.shortHash = c.hash.substring(0, 7);
          }

          // PR commits carry an inline "(#N)" that GitHub auto-links; keep it verbatim and skip
          // the sha link. direct pushes (no "(#N)") get the commit-sha link (see commitPartial)
          c.hasIssueRef = /\(#\d+\)/.test(c.subject || '');

          // comma-split the scope and bold each part -> "**a**, **b**" (rendered via scopeFmt)
          if (c.scope) {
            c.scopeFmt = c.scope.split(',').map(s => '**' + s.trim() + '**').join(', ');
          }

          // the parser may split trailing body lines into `footer` (e.g. a bullet containing an issue-like "#N");
          // fold body + footer back together, drop Signed-off-by and BREAKING CHANGE notes (rendered from `notes`),
          // collapse repeated blank lines and trim trailing ones
          const detail = stripNotes(
            [c.body, c.footer]
              .filter(Boolean)
              .join('\n')
              .split('\n')
              .filter(l => !isSignoff(l))
          ).filter((l, i, a) => !(l.trim() === '' && i > 0 && a[i - 1].trim() === ''));
          while (detail.length && detail[detail.length - 1].trim() === '') { detail.pop(); }
          if (detail.some(l => l.trim() !== '')) {
            // bullet body (`- ...`) -> 2-space sub-list right under the subject;
            // free-form body (no bullets) -> blank line + 4-space verbatim block
            const hasBullets = detail.some(l => /^\s*-\s+\S/.test(l));
            const indent = hasBullets ? '  ' : '    ';
            const block = detail.map(l => l.trim() === '' ? '' : indent + l).join('\n');
            c.body = hasBullets ? block : '\n' + block;
          } else {
            c.body = null;
          }
          c.footer = null;

          // drop Signed-off-by trailers from notes
          if (Array.isArray(c.notes)) {
            c.notes = c.notes
              .map(n => ({ ...n, text: stripSignoff(n.text) }))
              .filter(n => n.text);
          }

          return c;
        }
      }
    }],
    ["@semantic-release/changelog", Object.assign(
      { "changelogFile": CHANGELOG_FILE },
      CHANGELOG_TITLE ? { "changelogTitle": CHANGELOG_TITLE } : {}
    )],
    ["@semantic-release/exec", {
      "prepareCmd": "poetry version ${nextRelease.version} && poetry lock && sed -i \"s/rev: v[0-9]*\\.[0-9]*\\.[0-9]*/rev: v${nextRelease.version}/g\" README.md README.PYPI.md && sed -i \"s/cr-manager==[0-9]*\\.[0-9]*\\.[0-9]*/cr-manager==${nextRelease.version}/g\" README.md README.PYPI.md && ( pre-commit run --files CHANGELOG.md pyproject.toml poetry.lock README.md README.PYPI.md || true )"
    }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "pyproject.toml", "poetry.lock", "README.md", "README.PYPI.md"],
      "message": "chore(release): v${nextRelease.version}"
    }],
    "@semantic-release/github"
  ]
};
