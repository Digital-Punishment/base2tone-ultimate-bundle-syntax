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

class Base16Bundle {
  constructor() {
    this.createSelectListView = this.createSelectListView.bind(this);
  }

  static initClass() {

    this.prototype.config = require('./base16bundle_settings').config;
  }

  activate() {
    this.disposables = new CompositeDisposable;
    this.packageName = require('../package.json').name;
    this.disposables.add(atom.config.observe(`${this.packageName}.scheme`, () => this.enableConfigTheme()));
    this.disposables.add(atom.config.observe(`${this.packageName}.invertColors`, () => this.enableConfigTheme()));
    return this.disposables.add(atom.commands.add('atom-workspace', `${this.packageName}:select-theme`, this.createSelectListView));
  }

  deactivate() {
    return this.disposables.dispose();
  }

  enableConfigTheme() {
    const scheme = atom.config.get(`${this.packageName}.scheme`);
    const invertColors = atom.config.get(`${this.packageName}.invertColors`);
    return this.enableTheme(scheme, invertColors);
  }

  enableTheme(scheme, invertColors) {
    // No need to enable the theme if it is already active.
    if (!this.isPreviewConfirmed) { if (this.isActiveTheme(scheme, invertColors)) { return; } }
    try {
      // Write the requested theme to the `syntax-variables` file.
      fs.writeFileSync(this.getSyntaxVariablesPath(), this.getSyntaxVariablesContent(scheme, invertColors));
      const activePackages = atom.packages.getActivePackages();
      if ((activePackages.length === 0) || this.isPreview) {
        // Reload own stylesheets to apply the requested theme.
        atom.packages.getLoadedPackage(`${this.packageName}`).reloadStylesheets();
      } else {
        // Reload the stylesheets of all packages to apply the requested theme.
        for (let activePackage of Array.from(activePackages)) { activePackage.reloadStylesheets(); }
      }
      this.activeScheme = scheme;
      return this.activeStyle = invertColors;
    } catch (error) {
      // If unsuccessfull enable the default theme.
      return this.enableDefaultTheme();
    }
  }

  isActiveTheme(scheme, invertColors) {
    return (scheme === this.activeScheme) && (invertColors === this.activeStyle);
  }

  getSyntaxVariablesPath() {
    return path.join(__dirname, "..", "styles", "scheme.less");
  }

  getSyntaxVariablesContent(scheme, invertColors) {
    return `\
@base16-scheme: '${this.getNormalizedName(scheme)}';
@base16-invertColors: ${invertColors};

@import "schemes/@{base16-scheme}";
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
    const invertColors = atom.config.getDefault(`${this.packageName}.invertColors`);
    return this.setThemeConfig(scheme, invertColors);
  }

  setThemeConfig(scheme, invertColors) {
    atom.config.set(`${this.packageName}.scheme`, scheme);
    return atom.config.set(`${this.packageName}.invertColors`, invertColors);
  }

  createSelectListView() {
    const Base16BundleSelectListView = require('./base16bundle_select_list_view');
    const base16BundleSelectListView = new Base16BundleSelectListView(this);
    return base16BundleSelectListView.attach();
  }

  isConfigTheme(scheme, invertColors) {
    const configScheme = atom.config.get(`${this.packageName}.scheme`);
    const configInvert = atom.config.get(`${this.packageName}.invertColors`);
    return (scheme === configScheme) && (invertColors === configInvert);
  }
}
Base16Bundle.initClass();

module.exports = new Base16Bundle;
