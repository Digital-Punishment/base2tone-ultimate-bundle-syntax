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
    this.disposables.add(atom.config.observe(`${this.packageName}.invertColors`, () => this.enableConfigTheme()));
    return this.disposables.add(atom.commands.add('atom-workspace', `${this.packageName}:select-theme`, this.createSelectListView));
  }

  deactivate() {
    return this.disposables.dispose();
  }

  enableConfigTheme() {
    const scheme = atom.config.get(`${this.packageName}.scheme`);
    const contrastGutter = atom.config.get(`${this.packageName}.contrastGutter`);
    const invertColors = atom.config.get(`${this.packageName}.invertColors`);
    return this.enableTheme(scheme, contrastGutter, invertColors);
  }

  enableTheme(scheme, contrastGutter, invertColors) {
    // No need to enable the theme if it is already active.
    if (!this.isPreviewConfirmed) { if (this.isActiveTheme(scheme, contrastGutter, invertColors)) { return; } }
    try {
      // Write the requested theme to the `syntax-variables` file.
      fs.writeFileSync(this.getSyntaxVariablesPath(), this.getSyntaxVariablesContent(scheme, contrastGutter, invertColors));
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
      return this.activeInvertColors = invertColors;
    } catch (error) {
      // If unsuccessfull enable the default theme.
      return this.enableDefaultTheme();
    }
  }

  isActiveTheme(scheme, contrastGutter, invertColors) {
    return (scheme === this.activeScheme) && (contrastGutter === this.activeContrastGutter) && (invertColors === this.activeInvertColors);
  }

  getSyntaxVariablesPath() {
    return path.join(__dirname, "..", "styles", "scheme.less");
  }

  getSyntaxVariablesContent(scheme, contrastGutter, invertColors) {
    return `\
@base2tone-scheme: '${this.getNormalizedName(scheme)}';
@base2tone-style: 'dark';
@base2tone-contrastGutter: ${contrastGutter};

@import "schemes/@{base2tone-scheme}";
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
    const invertColors = atom.config.getDefault(`${this.packageName}.invertColors`);
    return this.setThemeConfig(scheme, contrastGutter, invertColors);
  }

  setThemeConfig(scheme, contrastGutter, invertColors) {
    atom.config.set(`${this.packageName}.scheme`, scheme);
    atom.config.set(`${this.packageName}.contrastGutter`, contrastGutter);
    return atom.config.set(`${this.packageName}.invertColors`, invertColors);
  }

  createSelectListView() {
    const Base2ToneBundleSelectListView = require('./base2tone_bundle_select_list_view');
    const base2ToneBundleSelectListView = new Base2ToneBundleSelectListView(this);
    return base2ToneBundleSelectListView.attach();
  }

  isConfigTheme(scheme, contrastGutter, invertColors) {
    const configScheme = atom.config.get(`${this.packageName}.scheme`);
    const configContrastGutter = atom.config.get(`${this.packageName}.contrastGutter`);
    const configInvertColors = atom.config.get(`${this.packageName}.invertColors`);
    return (scheme === configScheme) && (contrastGutter === configContrastGutter) && (invertColors === configInvertColors);
  }
}
Base2ToneBundle.initClass();

module.exports = new Base2ToneBundle;
