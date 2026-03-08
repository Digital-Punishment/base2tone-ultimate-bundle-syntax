/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/main/docs/suggestions.md
 */
const fs = require('fs');
const path = require('path');
const {CompositeDisposable} = require('atom');

class Base2ToneBundle {
  constructor() {
    this.createSelectListView = this.createSelectListView.bind(this);
  }

  static initClass() {

    this.prototype.config = require('./base2tone_bundle_settings').config;
  }

  activate() {
    this.disposables = new CompositeDisposable;
    this.packageName = require('../package.json').name;
    this.disposables.add(atom.config.observe(`${this.packageName}.scheme`, () => this.enableConfigTheme()));
    this.disposables.add(atom.config.observe(`${this.packageName}.contrastGutter`, () => this.enableConfigTheme()));
    this.disposables.add(atom.config.observe(`${this.packageName}.style`, () => this.enableConfigTheme()));
    return this.disposables.add(atom.commands.add('atom-workspace', `${this.packageName}:select-theme`, this.createSelectListView));
  }

  deactivate() {
    return this.disposables.dispose();
  }

  enableConfigTheme() {
    const scheme = atom.config.get(`${this.packageName}.scheme`);
    const contrastGutter = atom.config.get(`${this.packageName}.contrastGutter`);
    const style = atom.config.get(`${this.packageName}.style`);
    return this.enableTheme(scheme, contrastGutter, style);
  }

  enableTheme(scheme, contrastGutter, style) {
    // No need to enable the theme if it is already active.
    if (!this.isPreviewConfirmed) { if (this.isActiveTheme(scheme, contrastGutter, style)) { return; } }
    try {
      // Write the requested theme to the `syntax-variables` file.
      fs.writeFileSync(this.getSyntaxVariablesPath(), this.getSyntaxVariablesContent(scheme, contrastGutter, style));
      const activePackages = atom.packages.getActivePackages();
      if ((activePackages.length === 0) || this.isPreview) {
        // Reload own stylesheets to apply the requested theme.
        atom.packages.getLoadedPackage(`${this.packageName}`).reloadStylesheets();
      } else {
        // Reload the stylesheets of all packages to apply the requested theme.
        for (let activePackage of Array.from(activePackages)) { activePackage.reloadStylesheets(); }
      }
      this.activeScheme = scheme;
      this.activeContrastGutter = contrastGutter;
      return this.activeStyle = style;
    } catch (error) {
      // If unsuccessfull enable the default theme.
      return this.enableDefaultTheme();
    }
  }

  isActiveTheme(scheme, contrastGutter, style) {
    return (scheme === this.activeScheme) && (contrastGutter === this.activeContrastGutter) && (style === this.activeStyle);
  }

  getSyntaxVariablesPath() {
    return path.join(__dirname, "..", "styles", "syntax-variables.less");
  }

  getSyntaxVariablesContent(scheme, contrastGutter, style) {
    return `\
@base2tone-scheme: '${this.getNormalizedName(scheme)}';
@base2tone-style: '${this.getNormalizedName(style)}';
@base2tone-contrastGutter: ${contrastGutter};

@import "schemes/@{base2tone-scheme}";
@import "@{base2tone-style}/syntax";
@import "@{base2tone-style}/syntax-variables";
\
`;
  }

  getNormalizedName(name) {
    return `${name}`
      .replace(/\(/g, "")
      .replace(/\)/g, "")
      .replace(/,/g, "")
      .replace(/é/g, "e")
      .replace(/ /g, '-')
      .toLowerCase();
  }

  enableDefaultTheme() {
    const scheme = atom.config.getDefault(`${this.packageName}.scheme`);
    const contrastGutter = atom.config.getDefault(`${this.packageName}.contrastGutter`);
    const style = atom.config.getDefault(`${this.packageName}.style`);
    return this.setThemeConfig(scheme, contrastGutter, style);
  }

  setThemeConfig(scheme, contrastGutter, style) {
    atom.config.set(`${this.packageName}.scheme`, scheme);
    atom.config.set(`${this.packageName}.contrastGutter`, contrastGutter);
    return atom.config.set(`${this.packageName}.style`, style);
  }

  createSelectListView() {
    const Base2ToneBundleSelectListView = require('./base2tone_bundle_select_list_view');
    const base2ToneBundleSelectListView = new Base2ToneBundleSelectListView(this);
    return base2ToneBundleSelectListView.attach();
  }

  isConfigTheme(scheme, contrastGutter, style) {
    const configScheme = atom.config.get(`${this.packageName}.scheme`);
    const configContrastGutter = atom.config.get(`${this.packageName}.contrastGutter`);
    const configStyle = atom.config.get(`${this.packageName}.style`);
    return (scheme === configScheme) && (contrastGutter === configContrastGutter) && (style === configStyle);
  }
}
Base2ToneBundle.initClass();

module.exports = new Base2ToneBundle;
